from database import get_db_connection


def get_payment_methods(user_id):
    conn = get_db_connection()

    methods = conn.execute(
        """
        SELECT * FROM payment_methods
        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchall()

    conn.close()
    return [dict(method) for method in methods]


def add_payment_method(
    user_id,
    method_type,
    provider,
    masked_identifier,
    available_balance,
    fee=0,
    cashback=0,
    success_rate=0.94
):
    conn = get_db_connection()

    cursor = conn.execute(
        """
        INSERT INTO payment_methods
        (user_id, method_type, provider, masked_identifier, fee, cashback, success_rate, available_balance, is_default)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            method_type,
            provider,
            masked_identifier,
            fee,
            cashback,
            success_rate,
            available_balance,
            0
        )
    )

    conn.commit()
    method_id = cursor.lastrowid

    method = conn.execute(
        """
        SELECT * FROM payment_methods
        WHERE id = ? AND user_id = ?
        """,
        (method_id, user_id)
    ).fetchone()

    conn.close()
    return dict(method) if method else None


def get_user_rules(user_id):
    conn = get_db_connection()

    rules = conn.execute(
        """
        SELECT * FROM user_rules
        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchone()

    conn.close()
    return dict(rules) if rules else None


def get_user_balance(user_id):
    conn = get_db_connection()

    user = conn.execute(
        """
        SELECT balance FROM users
        WHERE id = ?
        """,
        (user_id,)
    ).fetchone()

    conn.close()
    return user["balance"] if user else 0
