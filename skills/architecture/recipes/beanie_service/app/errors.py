"""The base error and the categories the HTTP edge maps to a status.

Feature errors live in their feature's errors.py and subclass a category.
One handler per category is registered in main.py.
"""


class AppError(Exception):
    """Base of every error this service raises on purpose."""

    code = "app_error"


class NotFoundError(AppError):
    code = "not_found"


class ConflictError(AppError):
    code = "conflict"
