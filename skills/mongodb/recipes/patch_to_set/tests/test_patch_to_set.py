"""patch_to_set without a server. `after` and `changes` are built the way
the pydantic skill's apply_patch builds them: the merged, validated model,
and the nested dict of what the body set."""

from models import Address, Customer
from patch_to_set import patch_to_set

STORED = Customer(
    name="Ann",
    email="ann@example.com",
    address=Address(street="1 Main St", city="Paris", zip="75001"),
    tags=["a", "b"],
    prefs={"lang": "fr", "news": "no"},
)


def patched(**update) -> Customer:
    return Customer.model_validate(STORED.model_dump() | update)


def test_nested_field_becomes_a_dotted_path():
    after = patched(address={"street": "1 Main St", "city": "Lyon", "zip": "75001"})
    assert patch_to_set(STORED, after, {"address": {"city": "Lyon"}}) == {"address.city": "Lyon"}


def test_list_is_replaced_whole():
    after = patched(tags=["c"])
    assert patch_to_set(STORED, after, {"tags": ["c"]}) == {"tags": ["c"]}


def test_dict_field_is_replaced_whole_with_the_merged_value():
    # pydantic's deep_merge merges dicts key by key and changes holds only
    # the sent key; writing changes["prefs"] would drop "news".
    after = patched(prefs={"lang": "de", "news": "no"})
    assert patch_to_set(STORED, after, {"prefs": {"lang": "de"}}) == {
        "prefs": {"lang": "de", "news": "no"}
    }


def test_none_is_set_to_null_not_unset():
    after = patched(email=None)
    assert patch_to_set(STORED, after, {"email": None}) == {"email": None}


def test_nested_model_stored_as_null_is_written_whole():
    after = patched(billing={"street": "2 Side St", "city": "Nice", "zip": "06000"})
    changes = {"billing": {"street": "2 Side St", "city": "Nice", "zip": "06000"}}
    assert patch_to_set(STORED, after, changes) == {
        "billing": {"street": "2 Side St", "city": "Nice", "zip": "06000"}
    }


def test_nested_model_cleared_is_null():
    before = patched(billing={"street": "2 Side St", "city": "Nice", "zip": "06000"})
    after = before.model_copy(update={"billing": None})
    assert patch_to_set(before, after, {"billing": None}) == {"billing": None}


def test_unchanged_values_are_left_out():
    after = patched(name="Ann")
    assert patch_to_set(STORED, after, {"name": "Ann", "address": {"city": "Paris"}}) == {}


def test_value_comes_from_the_validated_model():
    # A validator may rewrite what the body sent; changes already holds the
    # validated value, and patch_to_set reads the model, not the body.
    after = patched(name="  Bea   Stone ")
    assert after.name == "Bea Stone"
    assert patch_to_set(STORED, after, {"name": "  Bea   Stone "}) == {"name": "Bea Stone"}


def test_alias_is_the_stored_name_when_asked():
    after = patched(displayName="Annie")
    assert patch_to_set(STORED, after, {"display": "Annie"}, by_alias=True) == {"displayName": "Annie"}
    assert patch_to_set(STORED, after, {"display": "Annie"}) == {"display": "Annie"}
