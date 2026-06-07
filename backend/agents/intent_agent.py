from llm.llm_client import call_llm_json
from llm.prompts import INTENT_PROMPT


def fallback_intent(user_message):
    message = user_message.lower()

    payment_words = ["pay", "make payment", "approve", "continue"]

    if "review" in message and ("subscription" in message or "waste" in message):
        intent = "analyze_subscriptions"

    elif any(word in message for word in payment_words):
        intent = "pay_bill"

    elif "subscription" in message or "subscriptions" in message or "waste" in message or "cancel" in message:
        intent = "analyze_subscriptions"

    elif "manage" in message or "autopilot" in message or "this week" in message:
        intent = "autopilot_payments"

    elif "risk" in message or "risky" in message or "safe" in message or "suspicious" in message:
        if "pay" in message or "manage" in message or "urgent" in message:
            intent = "pay_bill"
        else:
            intent = "analyze_payment_safety"

    elif "urgent" in message:
        intent = "pay_bill"

    elif "due" in message or "pending" in message or "show bills" in message:
        intent = "show_pending_bills"

    else:
        intent = "general_payment_advice"

    return {
        "intent": intent,
        "confidence": 75,
        "entities": {
            "bill_category": extract_category(message),
            "amount": None,
            "payee": None,
            "time_preference": "urgent" if "urgent" in message else None,
            "safety_condition": "safe" if "safe" in message else None
        },
        "reasoning": f"Rule-based fallback detected intent '{intent}'."
    }


def extract_category(message):
    if "electricity" in message or "power" in message or "bijli" in message:
        return "electricity"

    if "internet" in message or "wifi" in message or "fiber" in message or "airtel" in message:
        return "internet"

    if "credit card" in message or "hdfc" in message or "card bill" in message:
        return "credit_card"

    if "subscription" in message or "netflix" in message or "spotify" in message:
        return "subscription"

    if "shopping" in message or "qr" in message:
        return "shopping"

    return None


def detect_intent(user_message):
    fallback = fallback_intent(user_message)
    message = (user_message or "").lower()

    payment_words = ["pay", "make payment", "approve", "continue"]
    payment_requested = any(word in message for word in payment_words)

    if "waste" in message or ((("subscription" in message or "subscriptions" in message) and not payment_requested) or "review" in message):
        return {
            "agent": "Intent Agent",
            "intent": "analyze_subscriptions",
            "confidence": 95,
            "entities": fallback["entities"],
            "reasoning": "Deterministic context guard routed subscription or waste wording to subscription analysis."
        }

    prompt = INTENT_PROMPT.format(user_message=user_message)

    llm_result = call_llm_json(
        prompt=prompt,
        fallback=fallback,
        model_type="fast"
    )

    return {
        "agent": "Intent Agent",
        "intent": llm_result.get("intent", fallback["intent"]),
        "confidence": llm_result.get("confidence", fallback["confidence"]),
        "entities": llm_result.get("entities", fallback["entities"]),
        "reasoning": llm_result.get("reasoning", fallback["reasoning"])
    }
