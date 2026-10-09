import json
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from sqlalchemy import func, select

from app.ai.tools.registry import invoke_tool
from app.api.v1.deps import DbDep, PrincipalDep
from app.models.audit import AuditLog
from app.models.enums import Role
from app.core.config import get_settings
from app.models.knowledge import DocumentChunk, KnowledgeDocument
from app.models.organization import OrganizationMembership, OrganizationSettings, User
from app.models.ticket import Escalation
from app.schemas.admin import DocumentCreate, SettingsOut, SettingsUpdate
from app.services.audit import record_audit
from app.services.analytics import analytics_snapshot
from app.services.knowledge import ingest_document, safe_extract_text

router = APIRouter(tags=["workspace"])


@router.get("/analytics")
def analytics(db: DbDep, principal: PrincipalDep) -> dict:
    return analytics_snapshot(db, principal.organization_id)


@router.get("/knowledge")
def knowledge(db: DbDep, principal: PrincipalDep) -> list[dict]:
    docs = db.scalars(
        select(KnowledgeDocument).where(KnowledgeDocument.organization_id == principal.organization_id)
    ).all()
    return [
        {
            "id": doc.id,
            "title": doc.title,
            "status": doc.status,
            "archived": doc.archived,
            "chunk_count": db.scalar(select(func.count()).select_from(DocumentChunk).where(DocumentChunk.document_id == doc.id)) or 0,
        }
        for doc in docs
    ]


@router.post("/knowledge", status_code=201)
def create_document(payload: DocumentCreate, db: DbDep, principal: PrincipalDep) -> dict:
    if principal.role not in {Role.ORG_ADMIN, Role.SUPPORT_MANAGER}:
        raise HTTPException(status_code=403, detail="Only admins and managers can ingest documents")
    doc = ingest_document(db, principal.organization_id, payload.title, payload.source_type, payload.content)
    record_audit(db, principal.organization_id, principal.user.id, "document.ingested", "knowledge_document", doc.id)
    db.commit()
    return {"id": doc.id}


@router.post("/knowledge/upload", status_code=201)
async def upload_document(
    db: DbDep,
    principal: PrincipalDep,
    title: str = Form(...),
    file: UploadFile = File(...),
) -> dict:
    if principal.role not in {Role.ORG_ADMIN, Role.SUPPORT_MANAGER}:
        raise HTTPException(status_code=403, detail="Only admins and managers can ingest documents")
    try:
        raw = await file.read()
        text = safe_extract_text(file.filename or "upload.txt", file.content_type, raw, get_settings().max_upload_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=415, detail=str(exc))
    doc = ingest_document(db, principal.organization_id, title, file.content_type or "upload", text)
    record_audit(db, principal.organization_id, principal.user.id, "document.uploaded", "knowledge_document", doc.id)
    db.commit()
    return {"id": doc.id}


@router.post("/knowledge/{document_id}/archive")
def archive_document(document_id: str, db: DbDep, principal: PrincipalDep) -> dict:
    if principal.role not in {Role.ORG_ADMIN, Role.SUPPORT_MANAGER}:
        raise HTTPException(status_code=403, detail="Only admins and managers can archive documents")
    doc = db.scalar(
        select(KnowledgeDocument).where(
            KnowledgeDocument.id == document_id,
            KnowledgeDocument.organization_id == principal.organization_id,
        )
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc.archived = True
    doc.status = "archived"
    record_audit(db, principal.organization_id, principal.user.id, "document.archived", "knowledge_document", doc.id)
    db.commit()
    return {"status": "archived"}


@router.get("/escalations")
def escalations(db: DbDep, principal: PrincipalDep) -> list[dict]:
    rows = db.scalars(
        select(Escalation).where(Escalation.organization_id == principal.organization_id).order_by(Escalation.created_at.desc())
    ).all()
    return [
        {"id": row.id, "ticket_id": row.ticket_id, "reason": row.reason, "priority": row.priority, "status": row.status}
        for row in rows
    ]


@router.get("/users")
def users(db: DbDep, principal: PrincipalDep) -> list[dict]:
    if principal.role not in {Role.ORG_ADMIN, Role.SUPPORT_MANAGER}:
        raise HTTPException(status_code=403, detail="Insufficient role")
    rows = db.execute(
        select(User, OrganizationMembership).join(
            OrganizationMembership,
            OrganizationMembership.user_id == User.id,
        ).where(OrganizationMembership.organization_id == principal.organization_id)
    ).all()
    return [{"id": user.id, "email": user.email, "full_name": user.full_name, "role": member.role} for user, member in rows]


@router.get("/audit")
def audit(db: DbDep, principal: PrincipalDep) -> list[dict]:
    rows = db.scalars(
        select(AuditLog).where(AuditLog.organization_id == principal.organization_id).order_by(AuditLog.created_at.desc()).limit(100)
    ).all()
    return [{"action": row.action, "resource_type": row.resource_type, "resource_id": row.resource_id, "created_at": row.created_at} for row in rows]


@router.get("/settings", response_model=SettingsOut)
def settings(db: DbDep, principal: PrincipalDep) -> OrganizationSettings:
    row = db.scalar(select(OrganizationSettings).where(OrganizationSettings.organization_id == principal.organization_id))
    if not row:
        row = OrganizationSettings(organization_id=principal.organization_id)
        db.add(row)
        db.commit()
    return row


@router.patch("/settings", response_model=SettingsOut)
def update_settings(payload: SettingsUpdate, db: DbDep, principal: PrincipalDep) -> OrganizationSettings:
    if principal.role != Role.ORG_ADMIN:
        raise HTTPException(status_code=403, detail="Only organization admins can update settings")
    row = db.scalar(select(OrganizationSettings).where(OrganizationSettings.organization_id == principal.organization_id))
    if not row:
        row = OrganizationSettings(organization_id=principal.organization_id)
        db.add(row)
    if payload.autonomous_send_enabled is not None:
        row.autonomous_send_enabled = payload.autonomous_send_enabled
    if payload.retention_days is not None:
        row.retention_days = payload.retention_days
    if payload.model_settings is not None:
        row.model_settings = payload.model_settings
    record_audit(db, principal.organization_id, principal.user.id, "settings.updated", "organization_settings", row.id)
    db.commit()
    return row


@router.get("/evaluations/latest")
def latest_evaluation() -> dict:
    report_path = Path(__file__).resolve().parents[5] / "evaluation" / "reports" / "latest.json"
    repo_report_path = Path.cwd().parents[1] / "evaluation" / "reports" / "latest.json"
    for path in (report_path, repo_report_path):
        if path.exists():
            return json.loads(path.read_text())
    return {"status": "not_run", "message": "No evaluation report has been generated yet."}


@router.post("/tools/{tool_name}")
def tools(tool_name: str, payload: dict, db: DbDep, principal: PrincipalDep) -> dict:
    result = invoke_tool(db, principal, tool_name, payload, payload.get("ticket_id"))
    db.commit()
    return result
