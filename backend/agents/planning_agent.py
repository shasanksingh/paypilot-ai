from services.bill_service import get_pending_bills


def get_priority_score(bill):
    score = 0

    if bill["risk_hint"] == "normal":
        score += 50

    if bill["risk_hint"] == "suspicious":
        score -= 100

    if bill["risk_hint"] == "possible_duplicate":
        score -= 60

    if bill["risk_hint"] == "unused_subscription":
        score -= 40

    if bill["risk_hint"] == "vendor_change":
        score -= 75

    if bill["risk_hint"] == "invoice_spike":
        score -= 65

    if bill["risk_hint"] == "trial_renewal":
        score -= 35

    if bill["risk_hint"] == "geo_mismatch":
        score -= 90

    if bill["risk_hint"] == "cashflow_pressure":
        score -= 45

    if bill["amount"] <= 5000:
        score += 20

    if bill["amount"] > 10000:
        score -= 20

    return score


def create_payment_plan(user_id, intent_result):
    bills = get_pending_bills(user_id)

    plan = []

    for bill in bills:
        priority_score = get_priority_score(bill)

        if bill["risk_hint"] == "suspicious":
            priority = "blocked_until_verified"
        elif bill["risk_hint"] == "possible_duplicate":
            priority = "duplicate_review"
        elif bill["risk_hint"] == "unused_subscription":
            priority = "subscription_waste_review"
        elif bill["risk_hint"] == "vendor_change":
            priority = "vendor_verification_required"
        elif bill["risk_hint"] == "invoice_spike":
            priority = "invoice_spike_review"
        elif bill["risk_hint"] == "trial_renewal":
            priority = "trial_conversion_review"
        elif bill["risk_hint"] == "geo_mismatch":
            priority = "location_mismatch_review"
        elif bill["risk_hint"] == "cashflow_pressure":
            priority = "cashflow_buffer_review"
        elif bill["amount"] > 5000:
            priority = "approval_required"
        else:
            priority = "safe_to_pay"
            
        plan.append({
            "bill_id": bill["id"],
            "biller_name": bill["biller_name"],
            "category": bill["category"],
            "amount": bill["amount"],
            "due_date": bill["due_date"],
            "risk_hint": bill["risk_hint"],
            "priority": priority,
            "priority_score": priority_score,
            "reason": "Prioritized using safety, due date, amount, and risk hint."
        })

    plan.sort(
        key=lambda item: (
            -item["priority_score"],
            item["due_date"],
            item["amount"]
        )
    )

    return {
        "agent": "Planning Agent",
        "plan": plan,
        "reasoning": "Created safety-first payment plan. Suspicious bills are not automatically selected for payment."
    }
