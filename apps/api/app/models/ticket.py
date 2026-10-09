from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import IngestionSource, Priority, TicketStatus


def uuid() -> str:
    return str(uuid4())


class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = (UniqueConstraint("organization_id", "external_id", name="uq_ticket_org_external"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    customer_id: Mapped[str | None] = mapped_column(ForeignKey("customers.id"), index=True)
    external_id: Mapped[str | None] = mapped_column(String(120), index=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(60), default=TicketStatus.NEW.value, index=True)
    priority: Mapped[str] = mapped_column(String(40), default=Priority.NORMAL.value, index=True)
    source: Mapped[str] = mapped_column(String(40), default=IngestionSource.MANUAL.value)
    idempotency_key: Mapped[str | None] = mapped_column(String(160), index=True)
    processing_status: Mapped[str] = mapped_column(String(50), default="pending")
    processing_error: Mapped[str | None] = mapped_column(Text)
    ai_confidence: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("Message", back_populates="ticket")
    classifications = relationship("TicketClassification", back_populates="ticket")
    drafts = relationship("ResponseDraft", back_populates="ticket")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    ticket_id: Mapped[str] = mapped_column(ForeignKey("tickets.id"), index=True)
    sender_type: Mapped[str] = mapped_column(String(40), nullable=False)
    sender_name: Mapped[str | None] = mapped_column(String(160))
    body: Mapped[str] = mapped_column(Text, nullable=False)
    original_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="messages")


class TicketAssignment(Base):
    __tablename__ = "ticket_assignments"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    ticket_id: Mapped[str] = mapped_column(ForeignKey("tickets.id"), index=True)
    assigned_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    assigned_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TicketClassification(Base):
    __tablename__ = "ticket_classifications"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    ticket_id: Mapped[str] = mapped_column(ForeignKey("tickets.id"), index=True)
    issue_category: Mapped[str] = mapped_column(String(80), index=True)
    issue_subcategory: Mapped[str] = mapped_column(String(120))
    customer_intent: Mapped[str] = mapped_column(String(160))
    priority: Mapped[str] = mapped_column(String(40))
    sentiment: Mapped[str] = mapped_column(String(40))
    urgency: Mapped[str] = mapped_column(String(40))
    requires_human_review: Mapped[bool] = mapped_column(default=False)
    risk_flags: Mapped[list[str]] = mapped_column(JSON, default=list)
    summary: Mapped[str] = mapped_column(Text)
    classification_reasoning: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    model_name: Mapped[str] = mapped_column(String(120))
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="classifications")


class ResponseDraft(Base):
    __tablename__ = "response_drafts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    ticket_id: Mapped[str] = mapped_column(ForeignKey("tickets.id"), index=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    risk_flags: Mapped[list[str]] = mapped_column(JSON, default=list)
    quality: Mapped[dict] = mapped_column(JSON, default=dict)
    model_name: Mapped[str] = mapped_column(String(120))
    token_usage: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="drafts")
    citations = relationship("ResponseCitation", back_populates="draft")


class ResponseCitation(Base):
    __tablename__ = "response_citations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    draft_id: Mapped[str] = mapped_column(ForeignKey("response_drafts.id"), index=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("knowledge_documents.id"), index=True)
    chunk_id: Mapped[str] = mapped_column(ForeignKey("document_chunks.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    section: Mapped[str | None] = mapped_column(String(255))
    page_number: Mapped[int | None] = mapped_column(Integer)
    quote: Mapped[str] = mapped_column(Text)
    is_valid: Mapped[bool] = mapped_column(default=True)

    draft = relationship("ResponseDraft", back_populates="citations")


class Escalation(Base):
    __tablename__ = "escalations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    ticket_id: Mapped[str] = mapped_column(ForeignKey("tickets.id"), index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(40), default=Priority.HIGH.value)
    owner_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(40), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    ticket_id: Mapped[str] = mapped_column(ForeignKey("tickets.id"), index=True)
    request_type: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="pending")
    requested_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ToolInvocation(Base):
    __tablename__ = "tool_invocations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    ticket_id: Mapped[str | None] = mapped_column(ForeignKey("tickets.id"), index=True)
    tool_name: Mapped[str] = mapped_column(String(120), index=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    input_summary: Mapped[dict] = mapped_column(JSON, default=dict)
    result_summary: Mapped[dict] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ModelUsageRecord(Base):
    __tablename__ = "model_usage_records"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    ticket_id: Mapped[str | None] = mapped_column(ForeignKey("tickets.id"), index=True)
    provider: Mapped[str] = mapped_column(String(80))
    model_name: Mapped[str] = mapped_column(String(120))
    operation: Mapped[str] = mapped_column(String(80))
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost_usd: Mapped[float] = mapped_column(Float, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
