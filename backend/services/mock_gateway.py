import uuid

from database import get_db_connection


def execute_mock_payment(
    user_id,
    bill_id,
    amount,
    payment_method,
    risk_score,
    explanation,
    payment_method_id=None
):
    transaction_ref = "TXN_" + str(uuid.uuid4())[:8].upper()

    conn = get_db_connection()

    try:
        bill = conn.execute(
            """
            SELECT status FROM bills
            WHERE id = ? AND user_id = ?
            """,
            (bill_id, user_id)
        ).fetchone()

        if not bill:
            return {
                "transaction_ref": None,
                "status": "failed",
                "amount": amount,
                "payment_method": payment_method,
                "error": "Bill not found."
            }

        if bill["status"] != "pending":
            return {
                "transaction_ref": None,
                "status": "failed",
                "amount": amount,
                "payment_method": payment_method,
                "error": "Bill is no longer pending."
            }

        user = conn.execute(
            """
            SELECT balance FROM users
            WHERE id = ?
            """,
            (user_id,)
        ).fetchone()

        if not user or user["balance"] < amount:
            return {
                "transaction_ref": None,
                "status": "failed",
                "amount": amount,
                "payment_method": payment_method,
                "error": "Insufficient user balance."
            }

        cashback = 0

        if payment_method_id:
            method = conn.execute(
                """
                SELECT available_balance, cashback FROM payment_methods
                WHERE id = ? AND user_id = ?
                """,
                (payment_method_id, user_id)
            ).fetchone()

            if not method or method["available_balance"] < amount:
                return {
                    "transaction_ref": None,
                    "status": "failed",
                    "amount": amount,
                    "payment_method": payment_method,
                    "error": "Selected payment method no longer has enough available balance."
                }

            cashback = max(0, method["cashback"] or 0)

        conn.execute(
            """
            INSERT INTO transactions 
            (user_id, bill_id, amount, payment_method, status, risk_score, transaction_ref, explanation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                bill_id,
                amount,
                payment_method,
                "success",
                risk_score,
                transaction_ref,
                explanation
            )
        )

        conn.execute(
            """
            UPDATE bills
            SET status = 'paid'
            WHERE id = ? AND user_id = ?
            """,
            (bill_id, user_id)
        )

        conn.execute(
            """
            UPDATE users
            SET balance = balance - ? + ?
            WHERE id = ?
            """,
            (amount, cashback, user_id)
        )

        if payment_method_id:
            conn.execute(
                """
                UPDATE payment_methods
                SET available_balance = available_balance - ?
                WHERE id = ? AND user_id = ?
                """,
                (amount, payment_method_id, user_id)
            )

        conn.commit()

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    remaining_balance = user["balance"] - amount + cashback

    return {
        "transaction_ref": transaction_ref,
        "status": "success",
        "amount": amount,
        "payment_method": payment_method,
        "cashback": cashback,
        "net_balance_change": amount - cashback,
        "remaining_balance": remaining_balance
    }
