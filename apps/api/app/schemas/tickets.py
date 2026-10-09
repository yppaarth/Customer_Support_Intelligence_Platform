from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import IngestionSource, Priority, TicketStatus
from app.schemas.common import ORMModel


class TicketCreate(BaseModel):
    subject: str = Field(min_length=3, max_length=255)
    customer_email: str
    customer_name: str | None = None
    message: str = Field(min_length=3, max_length=8000)
    external_id: str | None = None
    source: IngestionSource = IngestionSource.MANUAL


class WebhookTicketCreate(TicketCreate):
    idempotency_key: str = Field(min_length=8, max_length=160)


class TicketListItem(ORMModel):
    id: str
    subject: str
    status: str
    priority: str
    ai_confidence: float | None
    created_at: datetime
    updated_at: datetime
    customer_name: str | None = None
    issue_category: str | None = None
    assigned_agent: str | None = None
    escalated: bool = False


class MessageOut(ORMModel):
    id: str
    sender_type: str
    sender_name: str | None
    body: str
    created_at: datetime


class ClassificationOut(ORMModel):
    issue_category: str
    issue_subcategory: str
    customer_intent: str
    priority: str
    sentiment: str
    urgency: str
    requires_human_review: bool
    risk_flags: list[str]
    summary: str
    classification_reasoning: str
    confidence: float
    model_name: str


class CitationOut(ORMModel):
    id: str
    title: str
    section: str | None
    page_number: int | None
    quote: str
    is_valid: bool


class DraftOut(ORMModel):
    id: str
    body: str
    status: str
    confidence: float
    risk_flags: list[str]
    quality: dict
    model_name: str
    citations: list[CitationOut] = []


class TicketDetail(ORMModel):
    id: str
    subject: str
    status: str
    priority: str
    ai_confidence: float | None
    created_at: datetime
    updated_at: datetime
    customer: dict | None
    order_context: list[dict]
    messages: list[MessageOut]
    classification: ClassificationOut | None
    latest_draft: DraftOut | None
    escalations: list[dict]
    audit: list[dict]


class TicketAction(BaseModel):
    status: TicketStatus | None = None
    priority: Priority | None = None
    assigned_user_id: str | None = None
    note: str | None = Field(default=None, max_length=4000)
    draft_body: str | None = Field(default=None, max_length=12000)


class BulkTicketAction(BaseModel):
    ticket_ids: list[str] = Field(min_length=1, max_length=100)
    assigned_user_id: str | None = None
    status: TicketStatus | None = None


class TicketImportResult(BaseModel):
    created: list[str]
    failed: list[dict]
