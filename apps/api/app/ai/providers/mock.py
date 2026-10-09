from app.schemas.ai import ClassificationResult, GeneratedDraft, RetrievedChunk

from .base import AIProvider


class MockAIProvider(AIProvider):
    name = "mock"

    async def classify(self, text: str) -> ClassificationResult:
        lowered = text.lower()
        category = "general_question"
        priority = "normal"
        risk_flags: list[str] = []
        sentiment = "neutral"
        if "refund" in lowered:
            category = "refund"
        if "late" in lowered or "delayed" in lowered or "tracking" in lowered:
            category = "shipping_delay"
        if "cancel" in lowered or "subscription" in lowered:
            category = "subscription"
        if "fraud" in lowered or "hacked" in lowered or "account takeover" in lowered:
            category = "security"
            priority = "urgent"
            risk_flags.append("security_or_fraud")
        if "double charged" in lowered or "billing" in lowered or "chargeback" in lowered:
            category = "billing"
        if "another customer" in lowered or "full card" in lowered:
            category = "unsupported"
            priority = "urgent"
            risk_flags.append("sensitive_data_request")
        if "lawyer" in lowered or "legal" in lowered:
            priority = "urgent"
            risk_flags.append("legal_threat")
        if "angry" in lowered or "furious" in lowered or "unacceptable" in lowered:
            sentiment = "angry"
        return ClassificationResult(
            issue_category=category,
            issue_subcategory=category.replace("_", " "),
            customer_intent="resolve_support_issue",
            priority=priority,
            sentiment=sentiment,
            urgency="high" if priority == "urgent" else "medium",
            requires_human_review=bool(risk_flags),
            risk_flags=risk_flags,
            summary=text[:220],
            classification_reasoning="Deterministic mock keyword classifier for local demos.",
            confidence=0.86 if not risk_flags else 0.79,
            model_name="mock-classifier-v1",
            metadata={"mock": True},
        )

    async def generate_draft(
        self,
        ticket_text: str,
        evidence: list[RetrievedChunk],
        customer_context: dict,
        risk_flags: list[str],
    ) -> GeneratedDraft:
        if not evidence:
            return GeneratedDraft(
                response_text=(
                    "Thanks for reaching out. I do not have enough approved policy evidence "
                    "to answer this safely, so I am escalating this for review."
                ),
                citations=[],
                confidence=0.25,
                risk_flags=[*risk_flags, "insufficient_evidence"],
                quality={"citation_validity": 1.0, "evidence_coverage": 0.0},
                token_usage={"prompt_tokens": 0, "completion_tokens": 0, "mock": True},
                model_name="mock-generator-v1",
            )
        source = evidence[0]
        order_hint = ""
        if customer_context.get("orders"):
            order_hint = f" I can see the latest order status is {customer_context['orders'][0]['status']}."
        return GeneratedDraft(
            response_text=(
                "Hi, thanks for contacting Northstar Commerce."
                f"{order_hint} Based on our current policy, {source.content[:280]} "
                "I have included the supporting source so an agent can verify this before sending."
            ),
            citations=evidence[:3],
            confidence=0.82 if not risk_flags else 0.62,
            risk_flags=risk_flags,
            quality={"citation_validity": 1.0, "evidence_coverage": min(1.0, len(evidence) / 3)},
            token_usage={"prompt_tokens": 0, "completion_tokens": 0, "mock": True},
            model_name="mock-generator-v1",
        )
