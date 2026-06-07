from datetime import date

from agents.intent_agent import detect_intent
from agents.planning_agent import create_payment_plan
from agents.bill_selector_agent import select_bill_for_request, subscription_matches_message
from agents.risk_agent import calculate_risk_score
from agents.optimizer_agent import select_best_payment_method
from agents.compliance_agent import check_compliance
from agents.approval_agent import create_approval_request
from agents.explainability_agent import generate_explanation
from agents.execution_agent import execute_payment
from agents.monitoring_agent import monitor_payment
from agents.reinforcement_agent import evaluate_policy_feedback, record_subscription_feedback

from services.bill_service import get_subscriptions, get_pending_bills, get_bill_by_id, create_pending_bill
from services.payment_service import get_user_balance
from services.transaction_service import log_agent_decision


def add_timeline(user_id, timeline, result):
    timeline.append(result)
    log_agent_decision(user_id, result)


def is_positive_follow_up(user_message):
    text = (user_message or "").lower().strip()
    return text in {"yes", "y", "ok", "okay", "continue", "approve", "pay", "pay it"} or "yes" in text


def is_negative_follow_up(user_message):
    text = (user_message or "").lower().strip()
    negative_words = ["no", "nope", "dont", "don't", "cancel", "stop", "not now"]
    return any(text == word or text.startswith(f"{word} ") for word in negative_words)


def wants_subscription_scan(user_message):
    text = (user_message or "").lower()
    return "waste" in text or "subscription" in text or "subscriptions" in text


def get_subscription_payment_bill(user_id, subscription):
    pending_bills = get_pending_bills(user_id)
    existing = next(
        (
            bill for bill in pending_bills
            if bill["biller_name"].lower() == subscription["merchant_name"].lower()
        ),
        None
    )

    if existing:
        return existing

    risk_hint = "unused_subscription" if subscription.get("waste_score", 0) >= 70 else "normal"

    return create_pending_bill(
        user_id=user_id,
        biller_name=subscription["merchant_name"],
        category="subscription",
        amount=subscription["amount"],
        due_date=date.today().isoformat(),
        is_recurring=1,
        risk_hint=risk_hint
    )


def get_blocked_payment_message(bill, risk_result):
    if risk_result.get("risk_level") == "high":
        return (
            "Risk is high, so this payment cannot be made. "
            "A review record is available so you can inspect the risk details."
        )

    if bill.get("risk_hint") == "possible_duplicate":
        return (
            "This looks like a duplicate payment, so it is blocked by default. "
            "A review record is available so you can inspect the duplicate signal."
        )

    return (
        "Payment is blocked by the Financial Safety Firewall. "
        "Please review the payment details in the Approval Queue before taking any action."
    )


def run_payment_orchestration(user_id, user_message, selected_bill_id=None, context=None):
    timeline = []
    context = context or {}

    if context.get("type") == "subscription_review" and is_positive_follow_up(user_message):
        subscription = context.get("subscription") or {}
        if subscription.get("merchant_name"):
            feedback_result = record_subscription_feedback(subscription, accepted=True)
            add_timeline(user_id, timeline, feedback_result)
            bill = get_subscription_payment_bill(user_id, subscription)
            selected_bill_id = bill["id"]
            user_message = f"Pay {subscription['merchant_name']}"

    elif context.get("type") == "subscription_review" and is_negative_follow_up(user_message):
        subscription = context.get("subscription") or {}
        if subscription.get("merchant_name"):
            feedback_result = record_subscription_feedback(subscription, accepted=False)
            add_timeline(user_id, timeline, feedback_result)

        if wants_subscription_scan(user_message):
            context = {}
            user_message = "Analyze my subscriptions and waste"
        else:
            return {
                "status": "subscription_declined",
                "message": (
                    f"Payment for {subscription.get('merchant_name', 'this subscription')} was cancelled. "
                    "No payment was made."
                ),
                "subscription": subscription,
                "timeline": timeline
            }

    intent_result = detect_intent(user_message)
    add_timeline(user_id, timeline, intent_result)

    if intent_result["intent"] == "show_pending_bills":
        bills = get_pending_bills(user_id)

        bills_result = {
            "agent": "Bills Agent",
            "bills": bills,
            "reasoning": "Fetched all pending bills for user."
        }

        add_timeline(user_id, timeline, bills_result)

        return {
            "status": "pending_bills",
            "message": "Pending bills fetched successfully.",
            "bills": bills,
            "timeline": timeline
        }

    if intent_result["intent"] == "analyze_subscriptions":
        subscriptions = get_subscriptions(user_id)
        focused_subscription = next(
            (
                subscription for subscription in subscriptions
                if subscription_matches_message(subscription, user_message)
            ),
            None
        )

        if focused_subscription:
            subscription_agent_result = {
                "agent": "Subscription Waste Agent",
                "subscriptions": [focused_subscription],
                "reasoning": f"Reviewed only {focused_subscription['merchant_name']} from the subscription list."
            }

            add_timeline(user_id, timeline, subscription_agent_result)

            return {
                "status": "subscription_review",
                "message": (
                    f"{focused_subscription['merchant_name']} reviewed. "
                    "If you want to pay this subscription, reply yes or use the suggestion below."
                ),
                "subscription": focused_subscription,
                "subscriptions": [focused_subscription],
                "timeline": timeline
            }

        subscription_agent_result = {
            "agent": "Subscription Waste Agent",
            "subscriptions": subscriptions,
            "reasoning": "Detected subscriptions with high waste score based on usage recency."
        }

        add_timeline(user_id, timeline, subscription_agent_result)

        return {
            "status": "subscription_analysis",
            "message": "Subscription waste analysis completed.",
            "subscriptions": subscriptions,
            "timeline": timeline
        }

    planning_result = create_payment_plan(user_id, intent_result)
    add_timeline(user_id, timeline, planning_result)

    bill, selector_result = select_bill_for_request(
        user_id=user_id,
        user_message=user_message,
        intent_result=intent_result,
        selected_bill_id=selected_bill_id
    )

    add_timeline(user_id, timeline, selector_result)

    if not bill:
        matched_subscription = selector_result.get("matched_subscription")
        suggestions = [
            "Open Subscriptions to review waste",
            "Show pending bills",
            "Pay my most urgent safe bill"
        ]

        return {
            "status": "no_bill_selected",
            "message": selector_result.get("selection_reason", "No pending bills found."),
            "plan": planning_result.get("plan", []),
            "matched_subscription": matched_subscription,
            "suggestions": suggestions,
            "timeline": timeline
        }

    risk_result = calculate_risk_score(bill)
    add_timeline(user_id, timeline, risk_result)

    reinforcement_result = evaluate_policy_feedback(user_id, bill, risk_result)
    add_timeline(user_id, timeline, reinforcement_result)

    optimizer_result = select_best_payment_method(user_id, bill["amount"], bill=bill)
    add_timeline(user_id, timeline, optimizer_result)

    user_balance = get_user_balance(user_id)

    compliance_result = check_compliance(
        user_id=user_id,
        user_balance=user_balance,
        amount=bill["amount"],
        risk_score=risk_result["risk_score"],
        bill=bill
    )

    add_timeline(user_id, timeline, compliance_result)

    explainability_result = generate_explanation(
        bill=bill,
        risk_result=risk_result,
        optimizer_result=optimizer_result,
        compliance_result=compliance_result
    )

    add_timeline(user_id, timeline, explainability_result)

    if not compliance_result["allowed"]:
        review_recommendation = (
            f"Blocked review: ₹{bill['amount']} to {bill['biller_name']} was stopped by the "
            "Financial Safety Firewall. Review risk reasons before any manual action."
        )
        review_result = create_approval_request(
            user_id=user_id,
            bill=bill,
            recommendation=review_recommendation,
            status="blocked_review"
        )
        add_timeline(user_id, timeline, review_result)

        return {
            "status": "blocked",
            "message": get_blocked_payment_message(bill, risk_result),
            "bill": bill,
            "plan": planning_result.get("plan", []),
            "risk": risk_result,
            "reinforcement": reinforcement_result,
            "optimizer": optimizer_result,
            "compliance": compliance_result,
            "review": review_result,
            "explanation": explainability_result["explanation"],
            "timeline": timeline
        }

    selected_method = optimizer_result.get("selected_method")

    if not selected_method:
        return {
            "status": "failed",
            "message": "No suitable payment method available.",
            "bill": bill,
            "plan": planning_result.get("plan", []),
            "risk": risk_result,
            "reinforcement": reinforcement_result,
            "optimizer": optimizer_result,
            "compliance": compliance_result,
            "explanation": explainability_result["explanation"],
            "timeline": timeline
        }

    recommendation = (
        f"Recommended to pay ₹{bill['amount']} to {bill['biller_name']} "
        f"using {selected_method['method_type']} via {selected_method['provider']}."
    )

    if not compliance_result["approval_required"]:
        execution_result = execute_payment(
            user_id=user_id,
            bill=bill,
            payment_method=selected_method,
            risk_score=risk_result["risk_score"],
            explanation=str(explainability_result["explanation"])
        )
        add_timeline(user_id, timeline, execution_result)

        monitoring_result = monitor_payment(execution_result["execution_result"])
        add_timeline(user_id, timeline, monitoring_result)

        if execution_result["execution_result"]["status"] != "success":
            return {
                "status": "failed",
                "message": "Payment could not be executed by the mock gateway.",
                "bill": bill,
                "plan": planning_result.get("plan", []),
                "risk": risk_result,
                "reinforcement": reinforcement_result,
                "optimizer": optimizer_result,
                "compliance": compliance_result,
                "execution": execution_result,
                "monitoring": monitoring_result,
                "explanation": explainability_result["explanation"],
                "timeline": timeline
            }

        return {
            "status": "auto_approved",
            "message": "Safe payment approved and executed by orchestration.",
            "bill": get_bill_by_id(bill["id"]) or bill,
            "plan": planning_result.get("plan", []),
            "risk": risk_result,
            "reinforcement": reinforcement_result,
            "optimizer": optimizer_result,
            "compliance": compliance_result,
            "execution": execution_result,
            "monitoring": monitoring_result,
            "recommendation": recommendation,
            "explanation": explainability_result["explanation"],
            "timeline": timeline
        }

    approval_result = create_approval_request(
        user_id=user_id,
        bill=bill,
        recommendation=recommendation
    )

    add_timeline(user_id, timeline, approval_result)

    return {
        "status": "approval_required",
        "message": "Payment is ready but requires human approval.",
        "bill": bill,
        "plan": planning_result.get("plan", []),
        "risk": risk_result,
        "reinforcement": reinforcement_result,
        "optimizer": optimizer_result,
        "compliance": compliance_result,
        "approval": approval_result,
        "explanation": explainability_result["explanation"],
        "timeline": timeline
    }
