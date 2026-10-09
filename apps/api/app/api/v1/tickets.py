from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.v1.deps import DbDep, PrincipalDep
from app.models.enums import TicketStatus
from app.models.ticket import Message, ResponseDraft, Ticket, TicketAssignment
from app.schemas.common import Page
from app.schemas.tickets import BulkTicketAction, TicketAction, TicketCreate, TicketDetail, TicketListItem, WebhookTicketCreate
from app.services.audit import record_audit
from app.services.tickets import build_ticket_detail, create_ticket, list_tickets, process_ticket

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("", response_model=Page[TicketListItem])
def index(
    db: DbDep,
    principal: PrincipalDep,
    status_filter: str | None = Query(default=None, alias="status"),
    priority: str | None = None,
    category: str | None = None,
    search: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Page[TicketListItem]:
    items, total = list_tickets(db, principal, status_filter, priority, category, search, limit, offset)
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.post("", status_code=status.HTTP_201_CREATED)
def create(payload: TicketCreate, db: DbDep, principal: PrincipalDep) -> dict:
    try:
        ticket = create_ticket(db, principal, payload)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    process_ticket(db, principal, ticket)
    db.commit()
    return {"id": ticket.id}


@router.post("/webhook", status_code=status.HTTP_202_ACCEPTED)
def webhook(payload: WebhookTicketCreate, db: DbDep, principal: PrincipalDep) -> dict:
    ticket = create_ticket(db, principal, payload, idempotency_key=payload.idempotency_key)
    if ticket.processing_status != "complete":
        process_ticket(db, principal, ticket)
    db.commit()
    return {"id": ticket.id, "idempotency_key": payload.idempotency_key}


@router.get("/{ticket_id}", response_model=TicketDetail)
def show(ticket_id: str, db: DbDep, principal: PrincipalDep) -> dict:
    detail = build_ticket_detail(db, principal, ticket_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return detail


@router.post("/{ticket_id}/regenerate")
def regenerate(ticket_id: str, db: DbDep, principal: PrincipalDep) -> dict:
    ticket = db.scalar(select(Ticket).where(Ticket.id == ticket_id, Ticket.organization_id == principal.organization_id))
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    draft = process_ticket(db, principal, ticket)
    db.commit()
    return {"status": "generated", "confidence": draft.confidence}


@router.post("/{ticket_id}/actions")
def action(ticket_id: str, payload: TicketAction, db: DbDep, principal: PrincipalDep) -> dict:
    if not principal.can_review():
        raise HTTPException(status_code=403, detail="Read-only role cannot mutate tickets")
    ticket = db.scalar(select(Ticket).where(Ticket.id == ticket_id, Ticket.organization_id == principal.organization_id))
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if payload.status:
        ticket.status = payload.status.value
    if payload.priority:
        ticket.priority = payload.priority.value
    if payload.assigned_user_id:
        db.add(
            TicketAssignment(
                organization_id=principal.organization_id,
                ticket_id=ticket.id,
                assigned_user_id=payload.assigned_user_id,
                assigned_by_user_id=principal.user.id,
            )
        )
    if payload.note:
        db.add(
            Message(
                organization_id=principal.organization_id,
                ticket_id=ticket.id,
                sender_type="internal_note",
                sender_name=principal.user.full_name,
                body=payload.note,
            )
        )
    if payload.draft_body:
        draft = db.scalar(
            select(ResponseDraft).where(ResponseDraft.ticket_id == ticket.id).order_by(ResponseDraft.created_at.desc())
        )
        if draft:
            draft.body = payload.draft_body
            draft.status = "edited"
    record_audit(db, principal.organization_id, principal.user.id, "ticket.action", "ticket", ticket.id, payload.model_dump(exclude_none=True))
    db.commit()
    return {"status": "ok"}


@router.post("/{ticket_id}/approve")
def approve(ticket_id: str, payload: TicketAction, db: DbDep, principal: PrincipalDep) -> dict:
    ticket = db.scalar(select(Ticket).where(Ticket.id == ticket_id, Ticket.organization_id == principal.organization_id))
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    draft = db.scalar(select(ResponseDraft).where(ResponseDraft.ticket_id == ticket.id).order_by(ResponseDraft.created_at.desc()))
    if not draft:
        raise HTTPException(status_code=409, detail="No draft to approve")
    if payload.draft_body:
        draft.body = payload.draft_body
    draft.status = "approved"
    ticket.status = TicketStatus.APPROVED.value
    record_audit(db, principal.organization_id, principal.user.id, "draft.approved", "ticket", ticket.id)
    db.commit()
    return {"status": "approved"}


@router.post("/bulk")
def bulk(payload: BulkTicketAction, db: DbDep, principal: PrincipalDep) -> dict:
    if not principal.can_review():
        raise HTTPException(status_code=403, detail="Read-only role cannot mutate tickets")
    tickets = db.scalars(
        select(Ticket).where(Ticket.organization_id == principal.organization_id, Ticket.id.in_(payload.ticket_ids))
    ).all()
    for ticket in tickets:
        if payload.status:
            ticket.status = payload.status.value
        if payload.assigned_user_id:
            db.add(
                TicketAssignment(
                    organization_id=principal.organization_id,
                    ticket_id=ticket.id,
                    assigned_user_id=payload.assigned_user_id,
                    assigned_by_user_id=principal.user.id,
                )
            )
    db.commit()
    return {"updated": len(tickets)}
