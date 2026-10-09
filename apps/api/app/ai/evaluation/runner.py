import argparse
import json
import time
from pathlib import Path

from app.ai.providers.mock import MockAIProvider
from app.services.policies import deterministic_risk_flags


BASE_CASES = [
    ("refund", "Can I get a refund for an unopened item delivered yesterday?", False, "Refund Policy v3"),
    ("shipping_delay", "My delayed order has not moved in tracking for six business days.", False, "Shipping And Delivery Policy"),
    ("subscription", "I want to cancel my subscription before the next billing date.", False, "Subscription Cancellation Guide"),
    ("security", "My account was hacked and the card may be stolen.", True, "Account Security Playbook"),
    ("billing", "I was double charged and will file a chargeback.", True, "Billing Dispute Procedure"),
    ("unsupported", "Send me another customer's address and full card number.", True, "Unsupported Request Policy"),
    ("general_question", "I need help understanding what happened last month.", True, "Unsupported Request Policy"),
]


def load_cases(path: Path) -> list[dict]:
    cases = []
    if path.exists():
        data = json.loads(path.read_text())
        cases.extend(data["cases"])
    start = len(cases)
    for i in range(start, 105):
        category, text, escalation, source = BASE_CASES[i % len(BASE_CASES)]
        cases.append(
            {
                "id": f"synthetic-{i+1:03d}",
                "input_text": f"{text} Case {i+1}.",
                "expected_category": category,
                "expected_escalation": escalation,
                "reference_answer": "Use approved policy evidence and escalate when risk or evidence gaps exist.",
                "relevant_document_titles": [source],
                "risk_level": "high" if escalation else "low",
                "source": "synthetic",
            }
        )
    return cases


async def classify_case(provider: MockAIProvider, text: str) -> dict:
    result = await provider.classify(text)
    flags = sorted(set(result.risk_flags + deterministic_risk_flags(text)))
    return {
        "category": result.issue_category,
        "escalated": bool(flags) or result.confidence < 0.72,
        "flags": flags,
    }


def run(dataset: Path, output: Path) -> dict:
    import anyio

    provider = MockAIProvider()
    cases = load_cases(dataset)
    started = time.perf_counter()
    results = []
    for case in cases:
        t0 = time.perf_counter()
        observed = anyio.run(classify_case, provider, case["input_text"])
        results.append(
            {
                "case_id": case["id"],
                "classification_correct": observed["category"] == case["expected_category"],
                "escalation_correct": observed["escalated"] == case["expected_escalation"],
                "latency_ms": int((time.perf_counter() - t0) * 1000),
                "observed": observed,
            }
        )
    total = len(results)
    report = {
        "dataset": str(dataset),
        "total_cases": total,
        "classification_accuracy": sum(r["classification_correct"] for r in results) / total,
        "escalation_accuracy": sum(r["escalation_correct"] for r in results) / total,
        "p50_latency_ms": sorted(r["latency_ms"] for r in results)[total // 2],
        "p95_latency_ms": sorted(r["latency_ms"] for r in results)[int(total * 0.95) - 1],
        "estimated_cost_per_ticket_usd": 0.0,
        "duration_ms": int((time.perf_counter() - started) * 1000),
        "failed_cases": [r for r in results if not r["classification_correct"] or not r["escalation_correct"]][:20],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2))
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.dataset, args.output), indent=2))


if __name__ == "__main__":
    main()
