import json

from app.schemas import UserOut
from app.service import greeting, user_response

RECORD = {"_id": 7, "login": "ada", "name": "Ada Lovelace", "email": "ada@example.com"}


def test_user_response_body():
    body = json.loads(user_response(RECORD))
    assert body == {"id": 7, "user_name": "ada", "display_name": "Ada Lovelace", "email": "ada@example.com"}


def test_greeting():
    out = UserOut(id=1, user_name="ada", display_name="Ada", email="a@example.com")
    assert greeting(out) == "Hello, Ada (ada)"
