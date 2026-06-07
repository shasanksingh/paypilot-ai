from database import get_db_connection


def log_agent_decision(user_id, agent_result):
    conn = get_db_connection()

    conn.execute(
        """
        INSERT INTO agent_logs
        (user_id, agent_name, input_summary, output_summary, reasoning)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            user_id,
            agent_result.get("agent", "Unknown Agent"),
            "Agent input processed",
            str(agent_result),
            agent_result.get("reasoning", "No reasoning available.")
        )
    )

    conn.commit()
    conn.close()


def get_transactions(user_id):
    conn = get_db_connection()

    transactions = conn.execute(
        """
        SELECT t.*, b.biller_name 
        FROM transactions t
        LEFT JOIN bills b ON t.bill_id = b.id
        WHERE t.user_id = ?
        ORDER BY t.created_at DESC
        """,
        (user_id,)
    ).fetchall()

    conn.close()
    return [dict(transaction) for transaction in transactions]


def get_agent_logs(user_id):
    conn = get_db_connection()

    logs = conn.execute(
        """
        SELECT * FROM agent_logs
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 80
        """,
        (user_id,)
    ).fetchall()

    conn.close()
    return [dict(log) for log in logs]