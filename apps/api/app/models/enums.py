from enum import StrEnum


class Role(StrEnum):
    ORG_ADMIN = "org_admin"
    SUPPORT_MANAGER = "support_manager"
    SUPPORT_AGENT = "support_agent"
    READ_ONLY_ANALYST = "read_only_analyst"


class TicketStatus(StrEnum):
    NEW = "new"
    TRIAGED = "triaged"
    WAITING_FOR_HUMAN_REVIEW = "waiting_for_human_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    SENT = "sent"
    RESOLVED = "resolved"
    REOPENED = "reopened"


class Priority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Sentiment(StrEnum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    ANGRY = "angry"


class IngestionSource(StrEnum):
    MANUAL = "manual"
    IMPORT = "import"
    WEBHOOK = "webhook"
    SEED = "seed"
