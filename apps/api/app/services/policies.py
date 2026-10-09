HIGH_RISK_TERMS = {
    "account_takeover": ["hacked", "account takeover", "login from", "password stolen"],
    "sensitive_personal_info": ["ssn", "passport", "credit card number", "full card"],
    "potential_fraud": ["fraud", "chargeback", "stolen", "scam"],
    "legal_threat": ["lawyer", "sue", "legal action", "attorney"],
    "high_impact_billing": ["double charged", "overcharged", "billing dispute"],
    "safety_complaint": ["injury", "unsafe", "fire", "shock"],
}


def deterministic_risk_flags(text: str) -> list[str]:
    lowered = text.lower()
    flags: list[str] = []
    for flag, terms in HIGH_RISK_TERMS.items():
        if any(term in lowered for term in terms):
            flags.append(flag)
    return flags


def should_escalate(confidence: float, retrieval_score: float, risk_flags: list[str]) -> tuple[bool, str]:
    if risk_flags:
        return True, f"High-risk policy triggered: {', '.join(sorted(set(risk_flags)))}"
    if retrieval_score < 0.24:
        return True, "Insufficient relevant evidence for grounded response"
    if confidence < 0.72:
        return True, "Draft confidence below configured threshold"
    return False, "No escalation required"
