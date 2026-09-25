from events.registry import handler


@handler("created")
def handle_created(event):
    return f"created {event['id']}"


@handler("refund")
def handle_refund(event):
    return f"refunded {event['id']}"
