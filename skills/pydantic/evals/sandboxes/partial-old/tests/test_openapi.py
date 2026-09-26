from users.openapi import patch_body_schema


def test_patch_body_fields_are_optional():
    assert patch_body_schema().get("required", []) == []
