from database import get_db_connection, init_db


def seed_database():
    init_db()
    conn = get_db_connection()

    conn.execute(
        """
        INSERT INTO users (name, email, balance)
        VALUES (?, ?, ?)
        """,
        ("Shashank", "shashank@example.com", 150000)
    )

    conn.execute(
        """
        INSERT INTO user_rules
        (user_id, minimum_safe_balance, approval_required_above, autopay_limit, block_high_risk, prefer_cashback)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (1, 25000, 5000, 2000, 1, 1)
    )

    bills = [
        (1, "Airtel Fiber", "internet", 999, "2026-05-20", "pending", 1, "normal"),
        (1, "Electricity Board", "electricity", 2450, "2026-05-19", "pending", 1, "normal"),
        (1, "HDFC Credit Card", "credit_card", 12000, "2026-05-25", "pending", 1, "normal"),
        (1, "Unknown QR Merchant", "shopping", 6500, "2026-05-18", "pending", 0, "suspicious"),
        (1, "Netflix", "subscription", 649, "2026-05-22", "pending", 1, "unused_subscription"),
        (1, "Duplicate Airtel Fiber", "internet", 999, "2026-05-21", "pending", 1, "possible_duplicate"),
        (1, "Indane Gas", "utilities", 1150, "2026-05-23", "pending", 0, "normal"),
        (1, "LIC Life Insurance", "insurance", 5200, "2026-05-26", "pending", 1, "normal"),
        (1, "Jio Mobile Postpaid", "mobile", 699, "2026-05-24", "pending", 1, "normal"),
        (1, "Metro Apartment Rent", "rent", 14000, "2026-05-28", "pending", 1, "normal"),
        (1, "Cloud GPU Labs", "software", 4999, "2026-05-27", "pending", 1, "unused_subscription"),
        (1, "Duplicate Electricity Board", "electricity", 2450, "2026-05-20", "pending", 1, "possible_duplicate"),
        (1, "PixelForge Studio", "software", 5500, "2026-05-21", "pending", 0, "vendor_change"),
        (1, "Global SaaS Labs USD", "software", 9500, "2026-05-24", "pending", 1, "geo_mismatch"),
        (1, "Trial CRM Renewal", "subscription", 4999, "2026-05-22", "pending", 1, "trial_renewal"),
        (1, "CoWork Hub Lease Adjustment", "rent", 9500, "2026-05-26", "pending", 1, "invoice_spike"),
        (1, "Freelancer Payroll Batch", "payroll", 8500, "2026-05-20", "pending", 0, "cashflow_pressure"),
        (1, "GST Advance Tax Challan", "tax", 4500, "2026-05-29", "pending", 0, "normal"),
        (1, "Charity QR Relief Fund", "donation", 3000, "2026-05-19", "pending", 0, "suspicious"),
        (1, "Water Authority", "utilities", 870, "2026-05-12", "paid", 1, "normal"),
        (1, "Amazon Prime", "subscription", 1499, "2026-05-10", "paid", 1, "normal"),
        (1, "SBI Credit Card", "credit_card", 9600, "2026-05-08", "paid", 1, "normal"),
        (1, "Vendor Onboarding Escrow", "software", 5400, "2026-05-06", "paid", 0, "vendor_change"),
        (1, "Payroll Reimbursement", "payroll", 7200, "2026-05-05", "paid", 0, "normal")
    ]

    conn.executemany(
        """
        INSERT INTO bills 
        (user_id, biller_name, category, amount, due_date, status, is_recurring, risk_hint)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        bills
    )

    subscriptions = [
        (1, "Netflix", 649, "monthly", 45, 82, "active"),
        (1, "Spotify", 119, "monthly", 3, 12, "active"),
        (1, "Cloud Storage Pro", 799, "monthly", 90, 91, "active"),
        (1, "Notion Plus", 850, "monthly", 18, 34, "active"),
        (1, "Fitness App Elite", 499, "monthly", 120, 94, "active"),
        (1, "Design Suite", 1299, "monthly", 7, 18, "active"),
        (1, "Language Learning Pro", 399, "monthly", 64, 72, "active"),
        (1, "Trial CRM Renewal", 12999, "annual", 0, 69, "active"),
        (1, "AI Meeting Notes", 1499, "monthly", 76, 88, "active"),
        (1, "Developer Sandbox Seats", 2199, "monthly", 34, 58, "active")
    ]

    conn.executemany(
        """
        INSERT INTO subscriptions
        (user_id, merchant_name, amount, billing_cycle, last_used_days_ago, waste_score, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        subscriptions
    )

    methods = [
        (1, "UPI", "Google Pay", "sha****@upi", 0, 0, 0.98, 30000, 1),
        (1, "Credit Card", "HDFC Bank", "**** **** **** 1234", 20, 100, 0.94, 80000, 0),
        (1, "Debit Card", "SBI", "**** **** **** 5678", 5, 0, 0.92, 45000, 0),
        (1, "Wallet", "Paytm", "paytm****91", 0, 10, 0.90, 5000, 0),
        (1, "Net Banking", "ICICI Bank", "ICICI **** 8821", 0, 20, 0.96, 65000, 0),
        (1, "BNPL", "PayLater Shield", "paylater****02", 75, 0, 0.86, 12000, 0),
        (1, "Corporate Card", "RazorpayX", "**** **** **** 4488", 35, 250, 0.93, 120000, 0),
        (1, "Escrow Wallet", "VendorShield", "escrow****74", 15, 0, 0.97, 40000, 0)
    ]

    conn.executemany(
        """
        INSERT INTO payment_methods
        (user_id, method_type, provider, masked_identifier, fee, cashback, success_rate, available_balance, is_default)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        methods
    )

    paid_bills = conn.execute(
        """
        SELECT id, biller_name, amount
        FROM bills
        WHERE user_id = ? AND status = 'paid'
        """,
        (1,)
    ).fetchall()

    transactions = [
        (
            1,
            bill["id"],
            bill["amount"],
            "UPI via Google Pay" if bill["amount"] < 2000 else "Net Banking via ICICI Bank",
            "success",
            12,
            f"TXN_SEED_{bill['id']:03d}",
            f"Seed transaction for {bill['biller_name']} completed after approval."
        )
        for bill in paid_bills
    ]

    conn.executemany(
        """
        INSERT INTO transactions
        (user_id, bill_id, amount, payment_method, status, risk_score, transaction_ref, explanation)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        transactions
    )

    conn.commit()
    conn.close()

    print("PayPilot AI database seeded successfully.")


if __name__ == "__main__":
    seed_database()
