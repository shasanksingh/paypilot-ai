from datetime import date

from flask import Flask, request, jsonify

try:
    from flask_cors import CORS
except Exception:
    CORS = None

from config import (
    USE_REMOTE_LLM,
    BASE_URL,
    API_KEY,
    MAIN_MODEL,
    FAST_MODEL,
    REASONING_MODEL,
    EMBEDDING_MODEL
)

from seed_data import seed_database
from database import get_db_connection

from agents.orchestrator import run_payment_orchestration
from agents.planning_agent import create_payment_plan
from agents.execution_agent import execute_payment
from agents.monitoring_agent import monitor_payment
from agents.risk_agent import calculate_risk_score, calculate_rule_risk_score
from agents.optimizer_agent import select_best_payment_method
from agents.explainability_agent import fallback_explanation, generate_explanation
from agents.compliance_agent import check_compliance
from agents.approval_agent import create_approval_request
from agents.reinforcement_agent import evaluate_policy_feedback

from services.bill_service import get_pending_bills, get_bill_by_id, get_subscriptions
from services.payment_service import get_payment_methods, get_user_balance, get_user_rules, add_payment_method
from services.transaction_service import get_transactions, get_agent_logs
from services.approval_service import get_approvals, get_approval_by_id, update_approval_status


app = Flask(__name__, static_folder="../frontend", static_url_path="")

RISKY_HINTS = {
    "suspicious",
    "unused_subscription",
    "possible_duplicate",
    "vendor_change",
    "invoice_spike",
    "trial_renewal",
    "geo_mismatch",
    "cashflow_pressure"
}

if CORS:
    CORS(app)


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


def log_step(message: str) -> None:
    print(message, flush=True)


def calculate_instant_risk_result(bill):
    risk_score, risk_reasons = calculate_rule_risk_score(bill)

    if risk_score >= 70:
        risk_level = "high"
    elif risk_score >= 40:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "agent": "Risk Agent",
        "risk_score": risk_score,
        "risk_level": risk_level,
        "risk_reasons": risk_reasons,
        "risk_summary": "Instant rule-based risk assessment completed.",
        "reasoning": "Prepared approval using deterministic risk rules to avoid remote LLM wait time."
    }


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


def mask_payment_identifier(method_type, raw_identifier):
    cleaned = "".join(char for char in str(raw_identifier or "") if char.isalnum() or char in {"@", "."})
    digits = "".join(char for char in str(raw_identifier or "") if char.isdigit())
    method = str(method_type or "").lower()

    if not cleaned and not digits:
        return "Protected details"

    if "upi" in method and "@" in str(raw_identifier or ""):
        handle, domain = str(raw_identifier).split("@", 1)
        return f"{handle[:2]}****@{domain}"

    last4 = (digits or cleaned)[-4:]

    if "card" in method:
        return f"**** **** **** {last4}"

    if "bank" in method or "account" in method:
        return f"Bank ****{last4}"

    if "wallet" in method:
        return f"wallet****{last4}"

    return f"****{last4}"


def update_review_status_for_bill(user_id, bill_id, status):
    conn = get_db_connection()

    conn.execute(
        """
        UPDATE approvals
        SET status = ?
        WHERE id = (
            SELECT id FROM approvals
            WHERE user_id = ? AND bill_id = ? AND status = 'blocked_review'
            ORDER BY created_at DESC
            LIMIT 1
        )
        """,
        (status, user_id, bill_id)
    )

    conn.commit()
    conn.close()


def build_bill_review(user_id, bill, use_remote_explanation=False):
    risk_result = calculate_risk_score(bill) if use_remote_explanation else calculate_instant_risk_result(bill)
    reinforcement_result = evaluate_policy_feedback(user_id, bill, risk_result)
    optimizer_result = select_best_payment_method(user_id, bill["amount"], bill=bill)
    user_balance = get_user_balance(user_id)

    compliance_result = check_compliance(
        user_id=user_id,
        user_balance=user_balance,
        amount=bill["amount"],
        risk_score=risk_result["risk_score"],
        bill=bill
    )

    explanation = (
        generate_explanation(
            bill=bill,
            risk_result=risk_result,
            optimizer_result=optimizer_result,
            compliance_result=compliance_result
        )["explanation"]
        if use_remote_explanation
        else fallback_explanation(
            bill=bill,
            risk_result=risk_result,
            optimizer_result=optimizer_result,
            compliance_result=compliance_result
        )
    )

    return risk_result, reinforcement_result, optimizer_result, compliance_result, explanation


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "message": "PayPilot AI backend is running",
        "system": "Agentic Payment Orchestration System",
        "remote_llm_enabled": USE_REMOTE_LLM and bool(API_KEY),
        "base_url": BASE_URL,
        "models": {
            "main_model": MAIN_MODEL,
            "fast_model": FAST_MODEL,
            "reasoning_model": REASONING_MODEL,
            "embedding_model": EMBEDDING_MODEL
        }
    })


@app.route("/api/setup", methods=["POST", "OPTIONS"])
def setup():
    if request.method == "OPTIONS":
        return jsonify({})

    seed_database()

    return jsonify({
        "message": "Database initialized and seeded successfully."
    })


@app.route("/api/dashboard", methods=["GET"])
def dashboard():
    user_id = 1

    bills = get_pending_bills(user_id)
    transactions = get_transactions(user_id)
    subscriptions = get_subscriptions(user_id)

    balance = get_user_balance(user_id)

    total_pending = sum(bill["amount"] for bill in bills)

    risky_bills = [bill for bill in bills if bill["risk_hint"] in RISKY_HINTS]
    high_value_bills = [bill for bill in bills if bill["amount"] > 10000]
    safe_payable_bills = [bill for bill in bills if bill["risk_hint"] == "normal"]
    today = date.today().isoformat()
    due_today_bills = [bill for bill in bills if bill["due_date"] <= today]

    return jsonify({
        "user": {
            "id": 1,
            "name": "Shashank",
            "balance": balance
        },
        "stats": {
            "pending_bills": len(bills),
            "total_pending_amount": total_pending,
            "risky_items": len(risky_bills),
            "completed_transactions": len(transactions),
            "subscriptions": len(subscriptions),
            "high_value_items": len(high_value_bills),
            "safe_payable_items": len(safe_payable_bills),
            "due_today_items": len(due_today_bills)
        },
        "bills": bills,
        "transactions": transactions,
        "subscriptions": subscriptions
    })


@app.route("/api/bills", methods=["GET"])
def bills():
    return jsonify(get_pending_bills(1))


@app.route("/api/account", methods=["GET"])
def account():
    user_id = 1
    balance = get_user_balance(user_id)
    rules = get_user_rules(user_id) or {}
    methods = get_payment_methods(user_id)
    bills = get_pending_bills(user_id)
    approvals = get_approvals(user_id)

    minimum_safe_balance = rules.get("minimum_safe_balance", 0)
    total_pending = sum(bill["amount"] for bill in bills)
    recommended_minimum_balance = max(minimum_safe_balance, round(total_pending * 0.2, -2))
    safe_buffer = balance - minimum_safe_balance
    balance_after_all_pending = balance - total_pending
    risky_bills = [bill for bill in bills if bill["risk_hint"] in RISKY_HINTS]
    pending_approvals = [item for item in approvals if item["status"] == "pending"]
    autopay_ready = [
        bill for bill in bills
        if bill["risk_hint"] == "normal" and bill["amount"] <= rules.get("autopay_limit", 0)
    ]

    return jsonify({
        "user": {
            "id": user_id,
            "name": "Shashank",
            "balance": balance
        },
        "rules": rules,
        "summary": {
            "minimum_safe_balance": minimum_safe_balance,
            "recommended_minimum_balance": recommended_minimum_balance,
            "safe_buffer": safe_buffer,
            "total_pending_amount": total_pending,
            "balance_after_all_pending": balance_after_all_pending,
            "pending_bills": len(bills),
            "risky_items": len(risky_bills),
            "pending_approvals": len(pending_approvals),
            "autopay_ready_items": len(autopay_ready),
            "method_count": len(methods)
        },
        "payment_methods": methods,
        "autopay_ready_bills": autopay_ready,
        "risk_watchlist": risky_bills[:6]
    })


@app.route("/api/bills/<int:bill_id>/analysis", methods=["GET"])
def bill_analysis(bill_id):
    user_id = 1

    bill = get_bill_by_id(bill_id)

    if not bill or bill["user_id"] != user_id:
        return jsonify({"error": "Bill not found"}), 404

    intent_result = {
        "agent": "Intent Agent",
        "intent": "payment_detail_analysis",
        "confidence": 100,
        "entities": {
            "bill_category": bill["category"],
            "amount": bill["amount"],
            "payee": bill["biller_name"],
            "time_preference": "selected_bill",
            "safety_condition": "safe"
        },
        "reasoning": "User opened a specific payment for direct risk and explainability review."
    }

    planning_result = create_payment_plan(user_id, intent_result)

    selector_result = {
        "agent": "Bill Selector Agent",
        "selected_bill_id": bill["id"],
        "selection_reason": "User opened this bill from the payment list.",
        "reasoning": "Direct payment-page analysis keeps the selected bill in focus."
    }

    risk_result = calculate_instant_risk_result(bill)
    reinforcement_result = evaluate_policy_feedback(user_id, bill, risk_result)
    optimizer_result = select_best_payment_method(user_id, bill["amount"], bill=bill)
    user_balance = get_user_balance(user_id)

    compliance_result = check_compliance(
        user_id=user_id,
        user_balance=user_balance,
        amount=bill["amount"],
        risk_score=risk_result["risk_score"],
        bill=bill
    )

    explainability_result = {
        "agent": "Explainability Agent",
        "explanation": fallback_explanation(
            bill=bill,
            risk_result=risk_result,
            optimizer_result=optimizer_result,
            compliance_result=compliance_result
        ),
        "reasoning": "Generated instant deterministic payment detail explanation."
    }

    timeline = [
        intent_result,
        planning_result,
        selector_result,
        risk_result,
        reinforcement_result,
        optimizer_result,
        compliance_result,
        explainability_result
    ]

    return jsonify({
        "status": "analysis_ready" if compliance_result["allowed"] else "blocked",
        "message": (
            "Payment analysis completed."
            if compliance_result["allowed"]
            else get_blocked_payment_message(bill, risk_result)
        ),
        "bill": bill,
        "plan": planning_result.get("plan", []),
        "risk": risk_result,
        "reinforcement": reinforcement_result,
        "optimizer": optimizer_result,
        "compliance": compliance_result,
        "explanation": explainability_result["explanation"],
        "timeline": timeline
    })


@app.route("/api/bills/<int:bill_id>/prepare-approval", methods=["POST", "OPTIONS"])
def prepare_bill_approval(bill_id):
    if request.method == "OPTIONS":
        return jsonify({})

    user_id = 1
    bill = get_bill_by_id(bill_id)

    if not bill or bill["user_id"] != user_id:
        return jsonify({"error": "Bill not found"}), 404

    if bill["status"] != "pending":
        return jsonify({"error": "Only pending bills can be prepared for approval"}), 400

    risk_result = calculate_instant_risk_result(bill)
    reinforcement_result = evaluate_policy_feedback(user_id, bill, risk_result)
    optimizer_result = select_best_payment_method(user_id, bill["amount"], bill=bill)
    user_balance = get_user_balance(user_id)

    compliance_result = check_compliance(
        user_id=user_id,
        user_balance=user_balance,
        amount=bill["amount"],
        risk_score=risk_result["risk_score"],
        bill=bill
    )

    explanation = fallback_explanation(
        bill=bill,
        risk_result=risk_result,
        optimizer_result=optimizer_result,
        compliance_result=compliance_result
    )

    timeline = [
        {
            "agent": "Risk Agent",
            "risk_score": risk_result["risk_score"],
            "risk_level": risk_result["risk_level"],
            "reasoning": risk_result["risk_summary"]
        },
        reinforcement_result,
        optimizer_result,
        compliance_result,
        {
            "agent": "Explainability Agent",
            "explanation": explanation,
            "reasoning": "Generated instant deterministic approval explanation without re-running remote LLM orchestration."
        }
    ]

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
        timeline.append(review_result)

        return jsonify({
            "status": "blocked",
            "message": get_blocked_payment_message(bill, risk_result),
            "bill": bill,
            "risk": risk_result,
            "reinforcement": reinforcement_result,
            "optimizer": optimizer_result,
            "compliance": compliance_result,
            "review": review_result,
            "explanation": explanation,
            "timeline": timeline
        })

    selected_method = optimizer_result.get("selected_method")

    if not selected_method:
        return jsonify({
            "status": "failed",
            "message": "No suitable payment method available.",
            "bill": bill,
            "risk": risk_result,
            "reinforcement": reinforcement_result,
            "optimizer": optimizer_result,
            "compliance": compliance_result,
            "explanation": explanation,
            "timeline": timeline
        }), 400

    if not compliance_result["approval_required"]:
        execution_result = execute_payment(
            user_id=user_id,
            bill=bill,
            payment_method=selected_method,
            risk_score=risk_result["risk_score"],
            explanation=str(explanation)
        )
        timeline.append(execution_result)

        monitoring_result = monitor_payment(execution_result["execution_result"])
        timeline.append(monitoring_result)

        if execution_result["execution_result"]["status"] != "success":
            return jsonify({
                "status": "failed",
                "message": "Payment could not be executed by the mock gateway.",
                "bill": bill,
                "risk": risk_result,
                "reinforcement": reinforcement_result,
                "optimizer": optimizer_result,
                "compliance": compliance_result,
                "execution": execution_result,
                "monitoring": monitoring_result,
                "explanation": explanation,
                "timeline": timeline
            }), 400

        return jsonify({
            "status": "auto_approved",
            "message": "Safe payment approved and executed by orchestration.",
            "bill": get_bill_by_id(bill["id"]) or bill,
            "risk": risk_result,
            "reinforcement": reinforcement_result,
            "optimizer": optimizer_result,
            "compliance": compliance_result,
            "execution": execution_result,
            "monitoring": monitoring_result,
            "explanation": explanation,
            "timeline": timeline
        })

    recommendation = (
        f"Recommended to pay ₹{bill['amount']} to {bill['biller_name']} "
        f"using {selected_method['method_type']} via {selected_method['provider']}."
    )

    approval_result = create_approval_request(
        user_id=user_id,
        bill=bill,
        recommendation=recommendation
    )

    timeline.append(approval_result)

    return jsonify({
        "status": "approval_required",
        "message": "Payment is ready but requires human approval.",
        "bill": bill,
        "risk": risk_result,
        "reinforcement": reinforcement_result,
        "optimizer": optimizer_result,
        "compliance": compliance_result,
        "approval": approval_result,
        "explanation": explanation,
        "timeline": timeline
    })


@app.route("/api/bills/<int:bill_id>/override-pay", methods=["POST", "OPTIONS"])
def override_blocked_bill_payment(bill_id):
    if request.method == "OPTIONS":
        return jsonify({})

    data = request.get_json() or {}

    if not data.get("confirm_risk"):
        return jsonify({
            "error": "Risk acknowledgement is required before paying a blocked payment."
        }), 400

    user_id = 1
    bill = get_bill_by_id(bill_id)

    if not bill or bill["user_id"] != user_id:
        return jsonify({"error": "Bill not found"}), 404

    if bill["status"] != "pending":
        return jsonify({"error": "Bill is no longer pending. Payment was not executed."}), 400

    risk_result, reinforcement_result, optimizer_result, compliance_result, explanation = build_bill_review(
        user_id=user_id,
        bill=bill,
        use_remote_explanation=True
    )

    selected_method = optimizer_result.get("selected_method")

    if not selected_method:
        return jsonify({
            "status": "failed",
            "message": "No suitable payment method available for this risk override.",
            "bill": bill,
            "risk": risk_result,
            "reinforcement": reinforcement_result,
            "optimizer": optimizer_result,
            "compliance": compliance_result,
            "explanation": explanation
        }), 400

    override_result = {
        "agent": "User Risk Override",
        "acknowledged": True,
        "reasoning": (
            "User reviewed the blocked payment, accepted the high-risk warning, "
            "and chose to pay at their own risk."
        )
    }

    execution_result = execute_payment(
        user_id=user_id,
        bill=bill,
        payment_method=selected_method,
        risk_score=risk_result["risk_score"],
        explanation=str(explanation)
    )

    monitoring_result = monitor_payment(execution_result["execution_result"])

    if execution_result["execution_result"]["status"] != "success":
        return jsonify({
            "status": "failed",
            "message": "Risk override was acknowledged, but the mock gateway could not execute the payment.",
            "bill": bill,
            "risk": risk_result,
            "reinforcement": reinforcement_result,
            "optimizer": optimizer_result,
            "compliance": compliance_result,
            "override": override_result,
            "execution": execution_result,
            "monitoring": monitoring_result,
            "explanation": explanation
        }), 400

    update_review_status_for_bill(user_id, bill_id, "approved")

    timeline = [
        risk_result,
        reinforcement_result,
        optimizer_result,
        compliance_result,
        {"agent": "Explainability Agent", "explanation": explanation, "reasoning": "Detailed blocked-payment explanation reviewed before override."},
        override_result,
        execution_result,
        monitoring_result
    ]

    return jsonify({
        "status": "override_approved",
        "message": "Payment executed after user accepted the risk warning.",
        "bill": get_bill_by_id(bill_id) or bill,
        "risk": risk_result,
        "reinforcement": reinforcement_result,
        "optimizer": optimizer_result,
        "compliance": compliance_result,
        "override": override_result,
        "execution": execution_result,
        "monitoring": monitoring_result,
        "explanation": explanation,
        "timeline": timeline
    })


@app.route("/api/bills/<int:bill_id>/cancel-risk-payment", methods=["POST", "OPTIONS"])
def cancel_blocked_bill_payment(bill_id):
    if request.method == "OPTIONS":
        return jsonify({})

    user_id = 1
    bill = get_bill_by_id(bill_id)

    if not bill or bill["user_id"] != user_id:
        return jsonify({"error": "Bill not found"}), 404

    update_review_status_for_bill(user_id, bill_id, "rejected")

    return jsonify({
        "status": "risk_payment_cancelled",
        "message": f"Payment for {bill['biller_name']} was cancelled. No payment was made.",
        "bill": bill
    })


@app.route("/api/subscriptions", methods=["GET"])
def subscriptions():
    return jsonify(get_subscriptions(1))


@app.route("/api/payment-methods", methods=["GET"])
def payment_methods():
    return jsonify(get_payment_methods(1))


@app.route("/api/payment-methods", methods=["POST", "OPTIONS"])
def create_payment_method():
    if request.method == "OPTIONS":
        return jsonify({})

    data = request.get_json() or {}
    method_type = str(data.get("method_type") or "").strip()
    provider = str(data.get("provider") or "").strip()
    raw_identifier = str(data.get("identifier") or "").strip()

    if not method_type or not provider or not raw_identifier:
        return jsonify({"error": "Method type, provider, and account/card details are required."}), 400

    try:
        available_balance = float(data.get("available_balance") or 0)
        cashback = float(data.get("cashback") or 0)
        fee = float(data.get("fee") or 0)
    except Exception:
        return jsonify({"error": "Limit, cashback, and fee must be valid numbers."}), 400

    if available_balance <= 0:
        return jsonify({"error": "Available limit must be greater than zero."}), 400

    method = add_payment_method(
        user_id=1,
        method_type=method_type,
        provider=provider,
        masked_identifier=mask_payment_identifier(method_type, raw_identifier),
        available_balance=available_balance,
        fee=max(0, fee),
        cashback=max(0, cashback)
    )

    return jsonify({
        "message": "Payment method added with protected details.",
        "payment_method": method
    }), 201


@app.route("/api/agent/chat", methods=["POST", "OPTIONS"])
def agent_chat():
    if request.method == "OPTIONS":
        return jsonify({})

    data = request.get_json() or {}

    user_message = data.get("message", "")
    selected_bill_id = data.get("bill_id")
    context = data.get("context") or {}

    result = run_payment_orchestration(
        user_id=1,
        user_message=user_message,
        selected_bill_id=selected_bill_id,
        context=context
    )

    return jsonify(result)


@app.route("/api/approvals", methods=["GET"])
def approvals():
    return jsonify(get_approvals(1))


@app.route("/api/approvals/<int:approval_id>/approve", methods=["POST", "OPTIONS"])
def approve_payment(approval_id):
    if request.method == "OPTIONS":
        return jsonify({})

    approval = get_approval_by_id(approval_id)

    if not approval:
        return jsonify({"error": "Approval request not found"}), 404

    if approval["status"] != "pending":
        return jsonify({"error": "Approval request is not pending"}), 400

    bill = get_bill_by_id(approval["bill_id"])

    if not bill:
        return jsonify({"error": "Bill not found"}), 404

    if bill["status"] != "pending":
        update_approval_status(approval_id, "blocked")

        return jsonify({
            "error": "Bill is no longer pending. Payment was not executed."
        }), 400

    risk_result = calculate_risk_score(bill)
    optimizer_result = select_best_payment_method(1, bill["amount"], bill=bill)
    user_balance = get_user_balance(1)

    compliance_result = check_compliance(
        user_id=1,
        user_balance=user_balance,
        amount=bill["amount"],
        risk_score=risk_result["risk_score"],
        bill=bill
    )

    if not compliance_result["allowed"]:
        update_approval_status(approval_id, "blocked")

        return jsonify({
            "message": get_blocked_payment_message(bill, risk_result),
            "compliance": compliance_result
        }), 400

    selected_method = optimizer_result.get("selected_method")

    if not selected_method:
        return jsonify({"error": "No suitable payment method found"}), 400

    explainability_result = generate_explanation(
        bill=bill,
        risk_result=risk_result,
        optimizer_result=optimizer_result,
        compliance_result=compliance_result
    )

    execution_result = execute_payment(
        user_id=1,
        bill=bill,
        payment_method=selected_method,
        risk_score=risk_result["risk_score"],
        explanation=str(explainability_result["explanation"])
    )

    monitoring_result = monitor_payment(execution_result["execution_result"])

    if execution_result["execution_result"]["status"] != "success":
        update_approval_status(approval_id, "blocked")

        return jsonify({
            "message": "Payment could not be executed by the mock gateway.",
            "execution": execution_result,
            "monitoring": monitoring_result,
            "explanation": explainability_result
        }), 400

    update_approval_status(approval_id, "approved")

    return jsonify({
        "message": "Payment approved and executed successfully.",
        "execution": execution_result,
        "monitoring": monitoring_result,
        "explanation": explainability_result
    })


@app.route("/api/approvals/<int:approval_id>/reject", methods=["POST", "OPTIONS"])
def reject_payment(approval_id):
    if request.method == "OPTIONS":
        return jsonify({})

    approval = get_approval_by_id(approval_id)

    if not approval:
        return jsonify({"error": "Approval request not found"}), 404

    if approval["status"] != "pending":
        return jsonify({"error": "Approval request is not pending"}), 400

    update_approval_status(approval_id, "rejected")

    return jsonify({
        "message": "Payment rejected successfully."
    })


@app.route("/api/transactions", methods=["GET"])
def transactions():
    return jsonify(get_transactions(1))


@app.route("/api/agent/logs", methods=["GET"])
def logs():
    return jsonify(get_agent_logs(1))


if __name__ == "__main__":
    log_step("Starting PayPilot AI...")
    log_step(f"Remote LLM enabled: {USE_REMOTE_LLM and bool(API_KEY)}")
    log_step(f"Main model: {MAIN_MODEL}")
    log_step(f"Fast model: {FAST_MODEL}")
    log_step(f"Reasoning model: {REASONING_MODEL}")
    log_step(f"Embedding model: {EMBEDDING_MODEL}")

    app.run(debug=True, port=5000)
