from billing_api import queue


def create_charge(request):
    charge = {"customer": request["customer"], "amount": request["amount"]}
    queue.publish("charges.created", charge)
    return {"status": "queued"}


ROUTES = {("POST", "/charges"): create_charge}


def main():
    print("serving", list(ROUTES))
