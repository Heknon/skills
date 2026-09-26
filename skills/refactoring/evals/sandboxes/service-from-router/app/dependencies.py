from app.repository import OrderRepository


def get_repo() -> OrderRepository:
    return OrderRepository()
