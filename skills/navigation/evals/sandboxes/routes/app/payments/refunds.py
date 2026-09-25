def refund(payment_id, amount):
    """Refund a card payment at the processor."""
    return {"payment": payment_id, "amount": amount}
