from database import get_db_connection


def get_pending_bills(user_id):
    conn = get_db_connection()

    bills = conn.execute(
        """
        SELECT * FROM bills
        WHERE user_id = ? AND status = 'pending'
        ORDER BY due_date ASC
        """,
        (user_id,)
    ).fetchall()

    conn.close()
    return [dict(bill) for bill in bills]


def get_bill_by_id(bill_id):
    conn = get_db_connection()

    bill = conn.execute(
        "SELECT * FROM bills WHERE id = ?",
        (bill_id,)
    ).fetchone()

    conn.close()
    return dict(bill) if bill else None


def create_pending_bill(user_id, biller_name, category, amount, due_date, is_recurring=0, risk_hint="normal"):
    conn = get_db_connection()

    cursor = conn.execute(
        """
        INSERT INTO bills
        (user_id, biller_name, category, amount, due_date, status, is_recurring, risk_hint)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, biller_name, category, amount, due_date, "pending", is_recurring, risk_hint)
    )

    conn.commit()
    bill_id = cursor.lastrowid
    conn.close()

    return get_bill_by_id(bill_id)


def mark_bill_paid(bill_id):
    conn = get_db_connection()

    conn.execute(
        "UPDATE bills SET status = 'paid' WHERE id = ?",
        (bill_id,)
    )

    conn.commit()
    conn.close()


def get_subscriptions(user_id):
    conn = get_db_connection()

    subscriptions = conn.execute(
        """
        SELECT * FROM subscriptions
        WHERE user_id = ?
        ORDER BY waste_score DESC
        """,
        (user_id,)
    ).fetchall()

    conn.close()
    return [dict(item) for item in subscriptions]
