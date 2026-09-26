from app.models import OrderPatch


def patch_to_dict(patch: OrderPatch) -> dict:
    """The fields the client sent, and only those."""
    raise NotImplementedError
