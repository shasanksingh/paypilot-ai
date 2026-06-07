from database import get_db_connection


def evaluate_policy_feedback(user_id, bill, risk_result):
    conn = get_db_connection()

    rows = conn.execute(
        """
        SELECT a.status, b.category, b.risk_hint
        FROM approvals a
        LEFT JOIN bills b ON a.bill_id = b.id
        WHERE a.user_id = ?
        """,
        (user_id,)
    ).fetchall()

    conn.close()

    category = bill["category"]
    risk_hint = bill["risk_hint"]
    related = [
        dict(row) for row in rows
        if row["category"] == category or row["risk_hint"] == risk_hint
    ]

    approved = len([row for row in related if row["status"] == "approved"])
    rejected = len([row for row in related if row["status"] == "rejected"])
    total = approved + rejected

    if total == 0:
        confidence = 50
        action = "neutral_review"
        summary = "No previous approval feedback exists for similar payments yet."
    else:
        confidence = round((approved / total) * 100)
        action = "prefer_approval" if confidence >= 70 else "ask_before_execution"
        summary = (
            f"Similar historical approvals: {approved} approved and {rejected} rejected, "
            f"giving {confidence}% approval confidence."
        )

    if risk_result.get("risk_score", 0) >= 40:
        action = "ask_before_execution"

    return {
        "agent": "Reinforcement Feedback Agent",
        "approval_confidence": confidence,
        "learned_action": action,
        "feedback_samples": total,
        "reasoning": (
            f"{summary} This lightweight RL-style signal uses human approval outcomes "
            "as reward feedback, then keeps risky payments in the approval loop."
        )
    }


def record_subscription_feedback(subscription, accepted):
    merchant = subscription.get("merchant_name", "selected subscription")
    reward = 1 if accepted else -1
    action = "continue_payment" if accepted else "cancel_payment"

    return {
        "agent": "Reinforcement Feedback Agent",
        "reward": reward,
        "learned_action": action,
        "feedback_target": merchant,
        "reasoning": (
            f"User {'accepted' if accepted else 'rejected'} payment after reviewing {merchant}. "
            "This response is treated as reinforcement feedback for future subscription payment prompts."
        )
    }
