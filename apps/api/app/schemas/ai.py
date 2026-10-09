from pydantic import BaseModel, Field


class ClassificationResult(BaseModel):
    issue_category: str
    issue_subcategory: str
    customer_intent: str
    priority: str
    sentiment: str
    urgency: str
    requires_human_review: bool
    risk_flags: list[str] = Field(default_factory=list)
    summary: str
    classification_reasoning: str
    confidence: float = Field(ge=0, le=1)
    model_name: str
    metadata: dict = Field(default_factory=dict)


class RetrievedChunk(BaseModel):
    chunk_id: str
    document_id: str
    title: str
    section: str | None = None
    page_number: int | None = None
    content: str
    score: float


class GeneratedDraft(BaseModel):
    response_text: str
    citations: list[RetrievedChunk]
    confidence: float = Field(ge=0, le=1)
    risk_flags: list[str] = Field(default_factory=list)
    quality: dict = Field(default_factory=dict)
    token_usage: dict = Field(default_factory=dict)
    model_name: str
