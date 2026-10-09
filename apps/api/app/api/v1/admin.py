from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.ai.tools.registry import invoke_tool
from app.api.v1.deps import DbDep, PrincipalDep
from app.models.audit import AuditLog
from app.models.enums import Role
from app.models.knowledge import DocumentChunk, KnowledgeDocument
from app.models.organization import OrganizationMembership, User
from app.models.ticket import Escalation
from app.services.analytics import analytics_snapshot

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
            "chunk_count": db.scalar(select(DocumentChunk).where(DocumentChunk.document_id == doc.id).count()) if False else len(doc.versions[0].chunks) if doc.versions else 0,
        }
        for doc in docs
    ]


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


@router.post("/tools/{tool_name}")
def tools(tool_name: str, payload: dict, db: DbDep, principal: PrincipalDep) -> dict:
    result = invoke_tool(db, principal, tool_name, payload, payload.get("ticket_id"))
    db.commit()
    return result
