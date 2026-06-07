from services.mock_gateway import execute_mock_payment


def execute_payment(user_id, bill, payment_method, risk_score, explanation):
    payment_method_label = (
        f"{payment_method['method_type']} via {payment_method['provider']}"
        if payment_method.get("provider")
        else payment_method["method_type"]
    )

    result = execute_mock_payment(
        user_id=user_id,
        bill_id=bill["id"],
        amount=bill["amount"],
        payment_method=payment_method_label,
        risk_score=risk_score,
        explanation=explanation,
        payment_method_id=payment_method.get("id")
    )

    return {
        "agent": "Execution Agent",
        "execution_result": result,
        "reasoning": "Payment executed through mock gateway after orchestration approval."
    }
