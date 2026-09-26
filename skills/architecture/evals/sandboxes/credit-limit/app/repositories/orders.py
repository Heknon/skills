from dataclasses import dataclass, field


@dataclass
class Customer:
    id: int
    credit_limit_cents: int
    open_total_cents: int = 0


@dataclass
class Order:
    id: int
    customer_id: int
    amount_cents: int


@dataclass
class OrderRepository:
    """In-memory storage; the SQL version keeps these method signatures."""

    customers: dict[int, Customer] = field(default_factory=dict)
    orders: list[Order] = field(default_factory=list)

    def get_customer(self, customer_id: int) -> Customer | None:
        return self.customers.get(customer_id)

    def add_order(self, customer_id: int, amount_cents: int) -> Order:
        order = Order(id=len(self.orders) + 1, customer_id=customer_id, amount_cents=amount_cents)
        self.orders.append(order)
        self.customers[customer_id].open_total_cents += amount_cents
        return order
