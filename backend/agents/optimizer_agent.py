from services.payment_service import get_payment_methods


def select_best_payment_method(user_id, amount, bill=None):
    methods = get_payment_methods(user_id)

    ranked_methods = []
    skipped_methods = []

    for method in methods:
        if bill and bill["category"] == "credit_card" and method["method_type"].lower() == "credit card":
            skipped_methods.append({
                "method_type": method["method_type"],
                "provider": method["provider"],
                "reason": "Credit card bills should not be paid using another credit card."
            })
            continue

        if method["available_balance"] < amount:
            skipped_methods.append({
                "method_type": method["method_type"],
                "provider": method["provider"],
                "reason": "Insufficient available balance for this bill."
            })
            continue

        net_benefit = method["cashback"] - method["fee"]

        safety_score = method["success_rate"] * 100

        final_score = net_benefit + safety_score

        ranked_methods.append({
            "id": method["id"],
            "method_type": method["method_type"],
            "provider": method["provider"],
            "masked_identifier": method["masked_identifier"],
            "fee": method["fee"],
            "cashback": method["cashback"],
            "success_rate": method["success_rate"],
            "net_benefit": net_benefit,
            "final_score": round(final_score, 2),
            "reason": f"Final score = success score {round(safety_score, 2)} + net benefit ₹{net_benefit}."
        })

    if not ranked_methods:
        return {
            "agent": "Optimizer Agent",
            "selected_method": None,
            "all_methods": [],
            "skipped_methods": skipped_methods,
            "reasoning": "No payment method passed balance and payment-type safety checks."
        }

    ranked_methods.sort(
        key=lambda item: item["final_score"],
        reverse=True
    )

    return {
        "agent": "Optimizer Agent",
        "selected_method": ranked_methods[0],
        "all_methods": ranked_methods,
        "skipped_methods": skipped_methods,
        "reasoning": "Selected best method using success rate, fee, cashback, and available balance."
    }
