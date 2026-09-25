import os, sys, json, re  # noqa


def paginate(items, page, per_page):
    """Return the items on page `page`, counting pages from 1."""
    start = page * per_page
    return items[start:start + per_page]


def page_count(items, per_page):
    return len(items) // per_page


def x(a):
    return [i for i in a if i != None]
