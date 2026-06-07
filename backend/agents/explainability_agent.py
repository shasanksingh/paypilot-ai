from llm.llm_client import call_llm_json
from llm.prompts import EXPLANATION_PROMPT


def fallback_explanation(bill, risk_result, optimizer_result, compliance_result):
    selected_method = optimizer_result.get("selected_method")

    if selected_method:
        method_text = (
            f"{selected_method['method_type']} via {selected_method['provider']} was selected "
            f"because it has final score {selected_method['final_score']}, "
            f"fee ₹{selected_method['fee']}, cashback ₹{selected_method['cashback']}, "
            f"and success rate {selected_method['success_rate']}."
        )
    else:
        method_text = "No suitable payment method was found."

    if not compliance_result["allowed"]:
        final_decision = "blocked"
    elif compliance_result["approval_required"]:
        final_decision = "approval_required"
    else:
        final_decision = "allowed"

    return {
        "summary": f"PayPilot analyzed payment to {bill['biller_name']} for ₹{bill['amount']}.",
        "why_this_payment": [
            f"Due date is {bill['due_date']}.",
            f"Category is {bill['category']}.",
            f"Current bill status is {bill['status']}."
        ],
        "risk_explanation": risk_result["risk_reasons"],
        "method_explanation": method_text,
        "policy_explanation": compliance_result["checks"],
        "final_decision": final_decision,
        "user_friendly_message": "PayPilot completed explainable payment analysis."
    }


def generate_explanation(bill, risk_result, optimizer_result, compliance_result):
    fallback = fallback_explanation(
        bill=bill,
        risk_result=risk_result,
        optimizer_result=optimizer_result,
        compliance_result=compliance_result
    )

    agent_context = {
        "bill": bill,
        "risk_result": risk_result,
        "optimizer_result": optimizer_result,
        "compliance_result": compliance_result
    }

    prompt = EXPLANATION_PROMPT.format(agent_context=agent_context)

    llm_result = call_llm_json(
        prompt=prompt,
        fallback=fallback,
        model_type="main"
    )

    return {
        "agent": "Explainability Agent",
        "explanation": llm_result,
        "reasoning": "Generated explainable AI decision using LLM with deterministic fallback."
    }