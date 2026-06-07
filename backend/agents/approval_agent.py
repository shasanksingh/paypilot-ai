from database import get_db_connection
from services.approval_service import get_pending_approval_for_bill


def create_approval_request(user_id, bill, recommendation, status="pending"):
    existing_approval = get_pending_approval_for_bill(user_id, bill["id"])

    if status == "pending" and existing_approval:
        return {
            "agent": "Approval Agent",
            "approval_id": existing_approval["id"],
            "status": "pending",
            "reused_existing": True,
            "reasoning": "Reused existing pending human approval request for this bill."
        }

    conn = get_db_connection()

    if status != "pending":
        existing_review = conn.execute(
            """
            SELECT * FROM approvals
            WHERE user_id = ? AND bill_id = ? AND status = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (user_id, bill["id"], status)
        ).fetchone()

        if existing_review:
            conn.close()
            return {
                "agent": "Approval Agent",
                "approval_id": existing_review["id"],
                "status": existing_review["status"],
                "reused_existing": True,
                "reasoning": "Reused existing blocked payment review record for this bill."
            }

    cursor = conn.execute(
        """
        INSERT INTO approvals (user_id, bill_id, amount, payee, recommendation, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            bill["id"],
            bill["amount"],
            bill["biller_name"],
            recommendation,
            status
        )
    )

    conn.commit()
    approval_id = cursor.lastrowid
    conn.close()

    return {
        "agent": "Approval Agent",
        "approval_id": approval_id,
        "status": status,
        "reused_existing": False,
        "reasoning": (
            "Created human approval request before payment execution."
            if status == "pending"
            else "Created blocked payment review record for human inspection."
        )
    }
