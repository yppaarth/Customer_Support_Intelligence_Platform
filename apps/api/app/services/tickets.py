from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.providers.openai_provider import get_ai_provider
from app.ai.retrieval.service import retrieve_chunks, validate_citations
from app.models.audit import AuditLog
from app.models.commerce import Customer, Order
from app.models.enums import IngestionSource, TicketStatus
from app.models.ticket import (
    Escalation,
    Message,
    ModelUsageRecord,
    ResponseCitation,
    ResponseDraft,
    Ticket,
    TicketAssignment,
    TicketClassification,
)
from app.schemas.ai import GeneratedDraft
from app.schemas.tickets import TicketCreate, TicketListItem
from app.security.auth import Principal
from app.services.audit import record_audit
from app.services.policies import deterministic_risk_flags, should_escalate


def get_or_create_customer(db: Session, organization_id: str, email: str, name: str | None) -> Customer:
    customer = db.scalar(
        select(Customer).where(Customer.organization_id == organization_id, Customer.email == email)
    )
    if customer:
        return customer
    customer = Customer(
        organization_id=organization_id,
        email=email,
        name=name or email.split("@")[0].replace(".", " ").title(),
    )
    db.add(customer)
    db.flush()
    return customer


def create_ticket(
    db: Session,
    principal: Principal,
    payload: TicketCreate,
    idempotency_key: str | None = None,
) -> Ticket:
    if not principal.can_write_tickets():
        raise PermissionError("Read-only users cannot create tickets")
    if idempotency_key:
        existing = db.scalar(
            select(Ticket).where(
                Ticket.organization_id == principal.organization_id,
                Ticket.idempotency_key == idempotency_key,
            )
        )
        if existing:
            return existing
    customer = get_or_create_customer(
        db, principal.organization_id, payload.customer_email, payload.customer_name
    )
    ticket = Ticket(
        organization_id=principal.organization_id,
        customer_id=customer.id,
        external_id=payload.external_id,
        subject=payload.subject,
        source=payload.source.value if isinstance(payload.source, IngestionSource) else str(payload.source),
        idempotency_key=idempotency_key,
    )
    db.add(ticket)
    db.flush()
    db.add(
        Message(
            organization_id=principal.organization_id,
            ticket_id=ticket.id,
            sender_type="customer",
            sender_name=customer.name,
            body=payload.message,
            original_payload=payload.model_dump(),
        )
    )
    record_audit(db, principal.organization_id, principal.user.id, "ticket.created", "ticket", ticket.id)
    return ticket


def list_tickets(
    db: Session,
    principal: Principal,
    status: str | None = None,
    priority: str | None = None,
    category: str | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[TicketListItem], int]:
    latest_cls = (
        select(TicketClassification)
        .where(TicketClassification.organization_id == principal.organization_id)
        .subquery()
    )
    stmt = select(Ticket, Customer).join(Customer, Customer.id == Ticket.customer_id, isouter=True).where(
        Ticket.organization_id == principal.organization_id
    )
    count_stmt = select(func.count()).select_from(Ticket).where(Ticket.organization_id == principal.organization_id)
    if status:
        stmt = stmt.where(Ticket.status == status)
        count_stmt = count_stmt.where(Ticket.status == status)
    if priority:
        stmt = stmt.where(Ticket.priority == priority)
        count_stmt = count_stmt.where(Ticket.priority == priority)
    if search:
        like = f"%{search}%"
        stmt = stmt.where(Ticket.subject.ilike(like))
        count_stmt = count_stmt.where(Ticket.subject.ilike(like))
    tickets = db.execute(stmt.order_by(Ticket.updated_at.desc()).limit(limit).offset(offset)).all()
    total = db.scalar(count_stmt) or 0
    items: list[TicketListItem] = []
    for ticket, customer in tickets:
        classification = db.scalar(
            select(TicketClassification)
            .where(TicketClassification.ticket_id == ticket.id)
            .order_by(TicketClassification.created_at.desc())
            .limit(1)
        )
        if category and (not classification or classification.issue_category != category):
            continue
        assignment = db.scalar(
            select(TicketAssignment).where(TicketAssignment.ticket_id == ticket.id).order_by(TicketAssignment.created_at.desc())
        )
        escalation = db.scalar(select(Escalation).where(Escalation.ticket_id == ticket.id, Escalation.status == "open"))
        items.append(
            TicketListItem(
                id=ticket.id,
                subject=ticket.subject,
                status=ticket.status,
                priority=ticket.priority,
                ai_confidence=ticket.ai_confidence,
                created_at=ticket.created_at,
                updated_at=ticket.updated_at,
                customer_name=customer.name if customer else None,
                issue_category=classification.issue_category if classification else None,
                assigned_agent=assignment.assigned_user_id if assignment else None,
                escalated=bool(escalation),
            )
        )
    return items, total


def process_ticket(db: Session, principal: Principal, ticket: Ticket) -> GeneratedDraft:
    db.flush()
    messages = db.scalars(
        select(Message).where(Message.ticket_id == ticket.id).order_by(Message.created_at.asc())
    ).all()
    ticket_text = "\n".join([ticket.subject, *[message.body for message in messages if message.sender_type == "customer"]])
    provider = get_ai_provider()
    import anyio

    classification = anyio.run(provider.classify, ticket_text)
    risk_flags = sorted(set(classification.risk_flags + deterministic_risk_flags(ticket_text)))
    classification.risk_flags = risk_flags
    classification.requires_human_review = classification.requires_human_review or bool(risk_flags)
    db.add(
        TicketClassification(
            organization_id=principal.organization_id,
            ticket_id=ticket.id,
            issue_category=classification.issue_category,
            issue_subcategory=classification.issue_subcategory,
            customer_intent=classification.customer_intent,
            priority=classification.priority,
            sentiment=classification.sentiment,
            urgency=classification.urgency,
            requires_human_review=classification.requires_human_review,
            risk_flags=classification.risk_flags,
            summary=classification.summary,
            classification_reasoning=classification.classification_reasoning,
            confidence=classification.confidence,
            model_name=classification.model_name,
            metadata_json=classification.metadata,
        )
    )
    ticket.priority = classification.priority
    evidence = retrieve_chunks(db, principal.organization_id, ticket_text)
    customer = db.get(Customer, ticket.customer_id) if ticket.customer_id else None
    orders = (
        db.scalars(select(Order).where(Order.customer_id == customer.id, Order.organization_id == principal.organization_id)).all()
        if customer
        else []
    )
    context = {
        "customer": {"id": customer.id, "tier": customer.tier} if customer else None,
        "orders": [{"order_number": o.order_number, "status": o.status} for o in orders],
    }
    draft = anyio.run(provider.generate_draft, ticket_text, evidence, context, risk_flags)
    citation_validity = validate_citations(draft.citations, evidence)
    quality = {**draft.quality, "all_citations_valid": all(citation_validity)}
    db_draft = ResponseDraft(
        organization_id=principal.organization_id,
        ticket_id=ticket.id,
        body=draft.response_text,
        status="waiting_for_human_review",
        confidence=draft.confidence,
        risk_flags=draft.risk_flags,
        quality=quality,
        model_name=draft.model_name,
        token_usage=draft.token_usage,
        created_by_user_id=principal.user.id,
    )
    db.add(db_draft)
    db.flush()
    for citation, is_valid in zip(draft.citations, citation_validity, strict=False):
        db.add(
            ResponseCitation(
                organization_id=principal.organization_id,
                draft_id=db_draft.id,
                document_id=citation.document_id,
                chunk_id=citation.chunk_id,
                title=citation.title,
                section=citation.section,
                page_number=citation.page_number,
                quote=citation.content[:500],
                is_valid=is_valid,
            )
        )
    top_score = evidence[0].score if evidence else 0.0
    escalate, reason = should_escalate(draft.confidence, top_score, draft.risk_flags)
    ticket.ai_confidence = draft.confidence
    ticket.status = TicketStatus.ESCALATED.value if escalate else TicketStatus.WAITING_FOR_HUMAN_REVIEW.value
    ticket.processing_status = "complete"
    if escalate:
        db.add(
            Escalation(
                organization_id=principal.organization_id,
                ticket_id=ticket.id,
                reason=reason,
                priority=ticket.priority,
            )
        )
    db.add(
        ModelUsageRecord(
            organization_id=principal.organization_id,
            ticket_id=ticket.id,
            provider=provider.name,
            model_name=draft.model_name,
            operation="ticket_processing",
            prompt_tokens=int(draft.token_usage.get("prompt_tokens", 0)),
            completion_tokens=int(draft.token_usage.get("completion_tokens", 0)),
            estimated_cost_usd=0.0,
            latency_ms=0,
        )
    )
    record_audit(
        db,
        principal.organization_id,
        principal.user.id,
        "ticket.processed",
        "ticket",
        ticket.id,
        {"escalated": escalate, "reason": reason},
    )
    return draft


def build_ticket_detail(db: Session, principal: Principal, ticket_id: str) -> dict:
    ticket = db.scalar(
        select(Ticket).where(Ticket.id == ticket_id, Ticket.organization_id == principal.organization_id)
    )
    if not ticket:
        return {}
    customer = db.get(Customer, ticket.customer_id) if ticket.customer_id else None
    messages = db.scalars(select(Message).where(Message.ticket_id == ticket.id).order_by(Message.created_at)).all()
    classification = db.scalar(
        select(TicketClassification).where(TicketClassification.ticket_id == ticket.id).order_by(TicketClassification.created_at.desc())
    )
    draft = db.scalar(
        select(ResponseDraft).where(ResponseDraft.ticket_id == ticket.id).order_by(ResponseDraft.created_at.desc())
    )
    citations = (
        db.scalars(select(ResponseCitation).where(ResponseCitation.draft_id == draft.id)).all() if draft else []
    )
    escalations = db.scalars(select(Escalation).where(Escalation.ticket_id == ticket.id)).all()
    audit = db.scalars(select(AuditLog).where(AuditLog.resource_id == ticket.id).order_by(AuditLog.created_at.desc())).all()
    orders = (
        db.scalars(select(Order).where(Order.customer_id == customer.id, Order.organization_id == principal.organization_id)).all()
        if customer
        else []
    )
    return {
        "id": ticket.id,
        "subject": ticket.subject,
        "status": ticket.status,
        "priority": ticket.priority,
        "ai_confidence": ticket.ai_confidence,
        "created_at": ticket.created_at,
        "updated_at": ticket.updated_at,
        "customer": {"id": customer.id, "name": customer.name, "email": customer.email, "tier": customer.tier} if customer else None,
        "order_context": [{"order_number": o.order_number, "status": o.status, "total_amount": float(o.total_amount)} for o in orders],
        "messages": messages,
        "classification": classification,
        "latest_draft": {**draft.__dict__, "citations": citations} if draft else None,
        "escalations": [{"id": e.id, "reason": e.reason, "priority": e.priority, "status": e.status, "created_at": e.created_at} for e in escalations],
        "audit": [{"action": a.action, "details": a.details, "created_at": a.created_at} for a in audit],
    }
