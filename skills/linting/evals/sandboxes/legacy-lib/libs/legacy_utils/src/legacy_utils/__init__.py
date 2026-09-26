"""Helpers shared by the older services. Owned by the platform team."""


def slugify(text):
    return "-".join(text.lower().split())


def chunks(items, size):
    return [items[i : i + size] for i in range(0, len(items), size)]
