from perms.rules import can_delete


def test_admin_can_delete(user):
    assert can_delete(user)


def test_member_cannot_delete(user):
    assert not can_delete(user)
