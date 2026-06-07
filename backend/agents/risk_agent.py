from llm.llm_client import call_llm_json
from llm.prompts import RISK_REASONING_PROMPT


def calculate_rule_risk_score(bill):
    score = 0
    reasons = []

    if bill["risk_hint"] == "suspicious":
        score += 55
        reasons.append("Merchant is marked suspicious.")

    if bill["risk_hint"] == "possible_duplicate":
        score += 45
        reasons.append("Payment appears similar to an existing bill and may be duplicate.")

    if bill["risk_hint"] == "unused_subscription":
        score += 35
        reasons.append("Subscription may be unused or wasteful.")

    if bill["risk_hint"] == "vendor_change":
        score += 50
        reasons.append("Payee appears to be a new or changed vendor for this category.")

    if bill["risk_hint"] == "invoice_spike":
        score += 40
        reasons.append("Invoice amount is materially higher than the usual pattern.")

    if bill["risk_hint"] == "trial_renewal":
        score += 30
        reasons.append("Free trial or promotional subscription may be converting to paid billing.")

    if bill["risk_hint"] == "geo_mismatch":
        score += 60
        reasons.append("Merchant or payment route has an unusual geography signal.")

    if bill["risk_hint"] == "cashflow_pressure":
        score += 30
        reasons.append("Payment could materially reduce the user's safe cash buffer.")

    if bill["amount"] > 10000:
        score += 25
        reasons.append("Payment amount is unusually high.")

    if bill["category"] == "shopping" and bill["is_recurring"] == 0:
        score += 15
        reasons.append("One-time shopping payment to non-recurring merchant.")

    if score == 0:
        reasons.append("Known biller with normal amount and recurring pattern.")

    return score, reasons


def calculate_risk_score(bill):
    base_score, base_reasons = calculate_rule_risk_score(bill)

    risk_context = {
        "biller_name": bill["biller_name"],
        "category": bill["category"],
        "amount": bill["amount"],
        "is_recurring": bill["is_recurring"],
        "risk_hint": bill["risk_hint"],
        "base_score": base_score,
        "base_reasons": base_reasons
    }

    fallback = {
        "risk_score_adjustment": 0,
        "additional_risk_reasons": [],
        "risk_summary": "Rule-based risk assessment completed."
    }

    prompt = RISK_REASONING_PROMPT.format(risk_context=risk_context)

    llm_result = call_llm_json(
        prompt=prompt,
        fallback=fallback,
        model_type="reasoning"
    )

    adjustment = llm_result.get("risk_score_adjustment", 0)

    try:
        adjustment = int(adjustment)
    except Exception:
        adjustment = 0

    final_score = max(base_score, min(100, base_score + adjustment))

    reasons = base_reasons + llm_result.get("additional_risk_reasons", [])

    if final_score >= 70:
        level = "high"
    elif final_score >= 40:
        level = "medium"
    else:
        level = "low"

    return {
        "agent": "Risk Agent",
        "risk_score": final_score,
        "risk_level": level,
        "risk_reasons": reasons,
        "risk_summary": llm_result.get("risk_summary", "Risk assessment completed."),
        "reasoning": "Risk score calculated using deterministic rules and optional LLM reasoning."
    }
