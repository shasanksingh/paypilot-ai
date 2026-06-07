from database import get_db_connection


def get_approvals(user_id):
    conn = get_db_connection()

    approvals = conn.execute(
        """
        SELECT * FROM approvals
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (user_id,)
    ).fetchall()

    conn.close()
    return [dict(item) for item in approvals]


def get_approval_by_id(approval_id):
    conn = get_db_connection()

    approval = conn.execute(
        """
        SELECT * FROM approvals
        WHERE id = ?
        """,
        (approval_id,)
    ).fetchone()

    conn.close()
    return dict(approval) if approval else None


def get_pending_approval_for_bill(user_id, bill_id):
    conn = get_db_connection()

    approval = conn.execute(
        """
        SELECT * FROM approvals
        WHERE user_id = ? AND bill_id = ? AND status = 'pending'
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (user_id, bill_id)
    ).fetchone()

    conn.close()
    return dict(approval) if approval else None


def update_approval_status(approval_id, status):
    conn = get_db_connection()

    conn.execute(
        """
        UPDATE approvals
        SET status = ?
        WHERE id = ?
        """,
        (status, approval_id)
    )

    conn.commit()
    conn.close()
