from typing import Annotated

from fastapi import Depends, Request

from app.repositories.orders import OrderRepository
from app.services.orders import OrderService


def get_order_repository(request: Request) -> OrderRepository:
    return request.app.state.orders


def get_order_service(repo: Annotated[OrderRepository, Depends(get_order_repository)]) -> OrderService:
    return OrderService(repo)
