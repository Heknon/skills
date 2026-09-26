import json
import logging

log = logging.getLogger(__name__)

_rendered = {}


def load_profile(user_id):
    """Stands in for a database read."""
    return {"id": user_id, "name": f"user {user_id}", "roles": ["reader"] * 20}


def render_profile(user_id, request_id):
    """The profile page of one user, as JSON. Rendering is cached per user."""
    key = (user_id, request_id)
    if key not in _rendered:
        log.debug("rendering user %s for request %s", user_id, request_id)
        _rendered[key] = json.dumps({"profile": load_profile(user_id)})
    return _rendered[key]
