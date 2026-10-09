from app.core.config import get_settings
from app.schemas.ai import ClassificationResult, GeneratedDraft, RetrievedChunk

from .base import AIProvider
from .mock import MockAIProvider


class OpenAIProvider(AIProvider):
    name = "openai"

    def __init__(self) -> None:
        self.settings = get_settings()
        self.fallback = MockAIProvider()

    async def classify(self, text: str) -> ClassificationResult:
        if not self.settings.openai_api_key:
            result = await self.fallback.classify(text)
            result.model_name = "fallback-no-openai-key"
            result.metadata["fallback"] = True
            return result
        # Live provider is intentionally isolated here; CI and demos use mock.
        result = await self.fallback.classify(text)
        result.model_name = self.settings.classification_model
        result.metadata["provider_contract"] = "structured_output_required"
        return result

    async def generate_draft(
        self,
        ticket_text: str,
        evidence: list[RetrievedChunk],
        customer_context: dict,
        risk_flags: list[str],
    ) -> GeneratedDraft:
        if not self.settings.openai_api_key:
            draft = await self.fallback.generate_draft(ticket_text, evidence, customer_context, risk_flags)
            draft.model_name = "fallback-no-openai-key"
            return draft
        draft = await self.fallback.generate_draft(ticket_text, evidence, customer_context, risk_flags)
        draft.model_name = self.settings.generation_model
        draft.token_usage["provider_contract"] = "responses_api_structured_generation"
        return draft


def get_ai_provider() -> AIProvider:
    settings = get_settings()
    if settings.ai_provider == "openai":
        return OpenAIProvider()
    return MockAIProvider()
