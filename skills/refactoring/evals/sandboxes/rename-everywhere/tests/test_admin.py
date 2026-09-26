from app.admin import AdminClient


def test_admin_get_user():
    assert AdminClient({"root": "Root"}).get_user("root") == "Root"
