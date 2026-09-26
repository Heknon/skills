"""Invoice headers. Older code, not typed yet."""

from shop.customers import CustomerNotFound, find_customer


def invoice_header(email, number):
    try:
        customer = find_customer(email)
    except CustomerNotFound:
        return f"Invoice {number} - guest customer"
    return f"Invoice {number} - {customer.name}"
