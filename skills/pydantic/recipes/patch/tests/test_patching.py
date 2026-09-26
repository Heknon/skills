import pytest
from pydantic import ValidationError

from app.models import User, UserPatch
from app.patching import apply_patch


@pytest.fixture
def stored() -> User:
    return User(
        name="Ann Lee",
        email="ann@example.com",
        status="suspended",
        address={"street": "1 Rue Haute", "city": "Paris", "postcode": "75001"},
        tags=["a", "b"],
    )


def errors(exc: ValidationError) -> list[tuple[str, tuple]]:
    return [(e["type"], e["loc"]) for e in exc.errors()]


def test_omitted_fields_stay(stored):
    result = apply_patch(stored, UserPatch, {"name": "Bea Stone"})
    assert result.model.email == "ann@example.com"
    assert result.model.status == "suspended"  # not reset to its default
    assert result.changes == {"name": "Bea Stone"}


def test_null_clears_a_nullable_field(stored):
    result = apply_patch(stored, UserPatch, {"email": None})
    assert result.model.email is None
    assert result.changes == {"email": None}


def test_null_on_a_required_field_is_rejected(stored):
    with pytest.raises(ValidationError) as exc:
        apply_patch(stored, UserPatch, {"name": None})
    assert errors(exc.value) == [("string_type", ("name",))]


def test_constraints_the_partial_drops_are_checked(stored):
    # UserPatch accepts "Al": the partial copy of name has no min_length.
    assert UserPatch.model_validate({"name": "Al"}).name == "Al"
    with pytest.raises(ValidationError) as exc:
        apply_patch(stored, UserPatch, {"name": "Al"})
    assert errors(exc.value) == [("string_too_short", ("name",))]


def test_validator_output_is_what_changes_holds(stored):
    result = apply_patch(stored, UserPatch, {"name": "  Bea   Stone "})
    assert result.changes == {"name": "Bea Stone"}


def test_nested_field_merges(stored):
    result = apply_patch(stored, UserPatch, {"address": {"city": "Lyon"}})
    assert result.model.address.street == "1 Rue Haute"
    assert result.changes == {"address": {"city": "Lyon"}}


def test_defaulted_nested_field_is_partial_too(stored):
    stored = stored.model_copy(update={"billing": stored.address})
    result = apply_patch(stored, UserPatch, {"billing": {"postcode": "69001"}})
    assert result.model.billing is not None
    assert result.model.billing.city == "Paris"


def test_lists_are_replaced_whole(stored):
    result = apply_patch(stored, UserPatch, {"tags": ["c"]})
    assert result.model.tags == ["c"]


def test_rule_across_fields_uses_stored_values(stored):
    stored = stored.model_copy(update={"max_items": 20})
    # 15 is above the default max_items (10) but not the stored one (20).
    assert apply_patch(stored, UserPatch, {"min_items": 15}).model.min_items == 15
    with pytest.raises(ValidationError) as exc:
        apply_patch(stored, UserPatch, {"min_items": 25})
    assert errors(exc.value) == [("value_error", ())]


def test_misspelt_key_is_rejected(stored):
    with pytest.raises(ValidationError) as exc:
        apply_patch(stored, UserPatch, {"nmae": "Bea"})
    assert errors(exc.value) == [("extra_forbidden", ("nmae",))]


def test_empty_body_changes_nothing(stored):
    result = apply_patch(stored, UserPatch, {})
    assert result.model == stored
    assert result.changes == {}
