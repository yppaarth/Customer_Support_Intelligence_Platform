from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.ticket import Escalation, ModelUsageRecord, ResponseDraft, Ticket


def analytics_snapshot(db: Session, organization_id: str) -> dict:
    total = db.scalar(select(func.count()).select_from(Ticket).where(Ticket.organization_id == organization_id)) or 0
    resolved = db.scalar(
        select(func.count()).select_from(Ticket).where(Ticket.organization_id == organization_id, Ticket.status == "resolved")
    ) or 0
    escalations = db.scalar(
        select(func.count()).select_from(Escalation).where(Escalation.organization_id == organization_id)
    ) or 0
    drafts = db.scalar(
        select(func.count()).select_from(ResponseDraft).where(ResponseDraft.organization_id == organization_id)
    ) or 0
    approved = db.scalar(
        select(func.count()).select_from(ResponseDraft).where(
            ResponseDraft.organization_id == organization_id, ResponseDraft.status == "approved"
        )
    ) or 0
    cost = db.scalar(
        select(func.coalesce(func.sum(ModelUsageRecord.estimated_cost_usd), 0)).where(
            ModelUsageRecord.organization_id == organization_id
        )
    ) or 0
    by_status = db.execute(
        select(Ticket.status, func.count()).where(Ticket.organization_id == organization_id).group_by(Ticket.status)
    ).all()
    by_priority = db.execute(
        select(Ticket.priority, func.count()).where(Ticket.organization_id == organization_id).group_by(Ticket.priority)
    ).all()
    return {
        "metric_source": "persisted_demo_data",
        "total_tickets": total,
        "open_tickets": max(total - resolved, 0),
        "resolved_tickets": resolved,
        "escalation_rate": escalations / total if total else 0,
        "ai_draft_acceptance_rate": approved / drafts if drafts else 0,
        "estimated_total_ai_cost_usd": float(cost),
        "tickets_by_status": [{"status": status, "count": count} for status, count in by_status],
        "tickets_by_priority": [{"priority": priority, "count": count} for priority, count in by_priority],
    }
