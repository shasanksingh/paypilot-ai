from services.payment_service import get_user_rules


def check_compliance(user_id, user_balance, amount, risk_score, bill=None):
    rules = get_user_rules(user_id)

    minimum_safe_balance = rules["minimum_safe_balance"] if rules else 10000
    approval_required_above = rules["approval_required_above"] if rules else 5000
    block_high_risk = rules["block_high_risk"] if rules else 1

    after_payment_balance = user_balance - amount

    checks = []
    allowed = True
    approval_required = False
    enhanced_review_required = False
    risk_hint = (bill or {}).get("risk_hint")

    if after_payment_balance < minimum_safe_balance:
        allowed = False
        checks.append(
            f"Payment would reduce balance to ₹{after_payment_balance}, below safe limit ₹{minimum_safe_balance}."
        )

    if risk_hint == "possible_duplicate":
        allowed = False
        approval_required = False
        checks.append("Possible duplicate payment is blocked by default.")

    if risk_score >= 70 and block_high_risk:
        allowed = False
        approval_required = False
        checks.append("High-risk payment is blocked by Financial Safety Firewall.")

    if risk_score >= 40 and allowed:
        approval_required = True
        checks.append("Risk signal is elevated, so human approval is required.")

    if amount > approval_required_above and allowed:
        approval_required = True
        enhanced_review_required = True
        checks.append(f"Payment amount is above approval limit ₹{approval_required_above}, so human approval is required.")

    if allowed:
        if approval_required:
            checks.append("Human approval is required before payment execution.")
        else:
            checks.append("Payment is low risk and allowed by policy, so orchestration may execute it automatically.")
        checks.append("Payment satisfies safety and policy rules.")

    return {
        "agent": "Compliance Agent",
        "allowed": allowed,
        "approval_required": approval_required,
        "enhanced_review_required": enhanced_review_required,
        "after_payment_balance": after_payment_balance,
        "checks": checks,
        "reasoning": "Compliance checked using balance safety, risk threshold, and user approval rules."
    }
