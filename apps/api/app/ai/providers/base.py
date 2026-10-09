from abc import ABC, abstractmethod

from app.schemas.ai import ClassificationResult, GeneratedDraft, RetrievedChunk


class AIProvider(ABC):
    name: str

    @abstractmethod
    async def classify(self, text: str) -> ClassificationResult:
        raise NotImplementedError

    @abstractmethod
    async def generate_draft(
        self,
        ticket_text: str,
        evidence: list[RetrievedChunk],
        customer_context: dict,
        risk_flags: list[str],
    ) -> GeneratedDraft:
        raise NotImplementedError
