from services.bill_service import get_pending_bills
from services.bill_service import get_subscriptions


SAFE_RISK_HINTS = {"normal"}
RISKY_RISK_HINTS = {
    "suspicious",
    "unused_subscription",
    "possible_duplicate",
    "vendor_change",
    "invoice_spike",
    "trial_renewal",
    "geo_mismatch",
    "cashflow_pressure"
}


def normalize_message(message):
    return (message or "").lower().strip()


def tokenize(value):
    cleaned = "".join(char.lower() if char.isalnum() else " " for char in str(value or ""))
    return [token for token in cleaned.split() if len(token) > 2]


def bill_matches_message(bill, message):
    return get_bill_match_score(bill, message) > 0


def get_bill_match_score(bill, message):
    text = normalize_message(message)

    biller = bill["biller_name"].lower()
    category = bill["category"].lower()
    biller_tokens = tokenize(biller)
    message_tokens = set(tokenize(text))
    score = 0

    if category in text:
        score += 12

    if biller in text:
        score += 100

    matched_biller_tokens = [token for token in biller_tokens if token in message_tokens]
    if biller_tokens and len(matched_biller_tokens) >= min(2, len(biller_tokens)):
        score += len(matched_biller_tokens) * 25
        if len(matched_biller_tokens) == len(biller_tokens):
            score += 25

    keywords = {
        "internet": ["internet", "wifi", "fiber", "broadband", "airtel"],
        "electricity": ["electricity", "power", "light", "bijli"],
        "credit_card": ["credit card", "card", "hdfc"],
        "subscription": ["subscription", "netflix", "spotify"],
        "shopping": ["shopping", "qr", "merchant"],
        "payroll": ["payroll", "salary", "freelancer", "contractor"],
        "software": ["software", "saas", "cloud", "crm", "gpu"],
        "rent": ["rent", "lease", "deposit"],
        "tax": ["tax", "gst", "compliance"],
        "donation": ["donation", "charity"]
    }

    for cat, words in keywords.items():
        if category == cat and any(word in text for word in words):
            score += 10

    return score


def subscription_matches_message(subscription, message):
    text = normalize_message(message)
    merchant = subscription["merchant_name"].lower()
    merchant_tokens = tokenize(merchant)
    message_tokens = set(tokenize(text))

    if merchant in text:
        return True

    return merchant_tokens and len([token for token in merchant_tokens if token in message_tokens]) >= min(2, len(merchant_tokens))


def looks_like_specific_payment_request(message):
    text = normalize_message(message)
    if not any(word in text for word in ["pay", "make payment", "approve", "continue"]):
        return False

    generic_terms = {
        "pay", "make", "payment", "please", "bill", "safe", "safely", "urgent",
        "most", "my", "the", "this", "continue", "approve", "approval", "now"
    }
    meaningful_tokens = [token for token in tokenize(text) if token not in generic_terms]
    return len(meaningful_tokens) >= 1


def is_safe_bill(bill):
    return bill["risk_hint"] in SAFE_RISK_HINTS


def is_risky_bill(bill):
    return bill["risk_hint"] in RISKY_RISK_HINTS


def select_bill_for_request(user_id, user_message, intent_result, selected_bill_id=None):
    """
    Selects the right bill based on user message and intent.
    This prevents every query from always selecting the earliest suspicious bill.
    """

    bills = get_pending_bills(user_id)
    message = normalize_message(user_message)
    intent = intent_result.get("intent")

    if not bills:
        return None, {
            "agent": "Bill Selector Agent",
            "selected_bill_id": None,
            "selection_reason": "No pending bills available.",
            "reasoning": "Bill selection could not run because there are no pending bills."
        }

    if selected_bill_id:
        selected = next((bill for bill in bills if bill["id"] == selected_bill_id), None)

        if not selected:
            return None, {
                "agent": "Bill Selector Agent",
                "selected_bill_id": selected_bill_id,
                "selection_reason": "Selected bill is not pending or does not exist.",
                "reasoning": "Direct bill selection failed safety validation before orchestration."
            }

        return selected, {
            "agent": "Bill Selector Agent",
            "selected_bill_id": selected_bill_id,
            "selection_reason": "User selected this bill directly from UI.",
            "reasoning": "Direct bill selection has highest priority."
        }

    matching_bills = [
        bill for bill in bills
        if bill_matches_message(bill, message)
    ]

    if matching_bills:
        matching_bills.sort(
            key=lambda bill: (
                -get_bill_match_score(bill, message),
                bill["due_date"],
                bill["amount"]
            )
        )

        selected = matching_bills[0]

        return selected, {
            "agent": "Bill Selector Agent",
            "selected_bill_id": selected["id"],
            "selection_reason": f"Selected bill because it matched the user request: {user_message}",
            "reasoning": "Bill selected using category, biller name, and natural language keywords."
        }

    matching_subscriptions = [
        subscription for subscription in get_subscriptions(user_id)
        if subscription_matches_message(subscription, message)
    ]

    if matching_subscriptions:
        subscription = matching_subscriptions[0]
        return None, {
            "agent": "Bill Selector Agent",
            "selected_bill_id": None,
            "matched_subscription": subscription,
            "selection_reason": (
                f"{subscription['merchant_name']} is present in the subscription waste list, "
                "but there is no pending bill for it to pay."
            ),
            "reasoning": "Subscription follow-up matched a subscription record, so PayPilot did not fall back to an unrelated bill."
        }

    if looks_like_specific_payment_request(message):
        return None, {
            "agent": "Bill Selector Agent",
            "selected_bill_id": None,
            "selection_reason": "No pending bill matched the named payment request.",
            "reasoning": "A specific payment name was requested, so PayPilot refused to fall back to another bill."
        }

    if "risk" in message or "risky" in message or "suspicious" in message or intent == "analyze_payment_safety":
        risky_bills = [bill for bill in bills if is_risky_bill(bill)]

        if risky_bills:
            risky_bills.sort(
                key=lambda bill: (
                    get_risk_sort_rank(bill["risk_hint"]),
                    bill["due_date"]
                )
            )

            selected = risky_bills[0]

            return selected, {
                "agent": "Bill Selector Agent",
                "selected_bill_id": selected["id"],
                "selection_reason": "Selected the riskiest pending bill for safety analysis.",
                "reasoning": "Risk scan query should analyze risky bills instead of safe bills."
            }

    if "urgent" in message or "due" in message or "pay" in message or "manage" in message or "autopilot" in message:
        safe_bills = [bill for bill in bills if is_safe_bill(bill)]

        if safe_bills:
            safe_bills.sort(key=lambda bill: (bill["due_date"], bill["amount"]))

            selected = safe_bills[0]

            return selected, {
                "agent": "Bill Selector Agent",
                "selected_bill_id": selected["id"],
                "selection_reason": "Selected earliest safe payable bill instead of suspicious bill.",
                "reasoning": "For payment execution flows, PayPilot avoids suspicious bills and chooses a safe bill first."
            }

    bills.sort(key=lambda bill: (bill["due_date"], bill["amount"]))

    selected = bills[0]

    return selected, {
        "agent": "Bill Selector Agent",
        "selected_bill_id": selected["id"],
        "selection_reason": "Selected earliest pending bill as fallback.",
        "reasoning": "Fallback bill selection used due date ordering."
    }


def get_risk_sort_rank(risk_hint):
    ranks = {
        "suspicious": 0,
        "geo_mismatch": 1,
        "vendor_change": 2,
        "invoice_spike": 3,
        "possible_duplicate": 4,
        "cashflow_pressure": 5,
        "trial_renewal": 6,
        "unused_subscription": 7
    }
    return ranks.get(risk_hint, 9)
