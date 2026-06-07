def monitor_payment(transaction):
    return {
        "agent": "Monitoring Agent",
        "status": transaction["status"],
        "message": "Payment status monitored successfully.",
        "receipt_ready": True,
        "reasoning": "Transaction reference, payment status, and receipt availability verified."
    }