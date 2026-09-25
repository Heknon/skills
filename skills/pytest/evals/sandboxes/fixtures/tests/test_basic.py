from perms.rules import can_delete


def test_member_basic(user):
    assert not can_delete(user)
