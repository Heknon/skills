"""The same rules against a real server (development only).
Set MONGODB_URI to run them; they use the database patch_to_set_test."""

import os

import pytest
from pymongo import MongoClient

from models import Address, Customer
from patch_to_set import patch_to_set, write_patch

URI = os.environ.get("MONGODB_URI")
pytestmark = pytest.mark.skipif(not URI, reason="needs MONGODB_URI (a development server)")


@pytest.fixture
def coll():
    client = MongoClient(URI)
    c = client["patch_to_set_test"]["customers"]
    c.drop()
    c.insert_one({"_id": 1, "name": "Ann", "email": "ann@example.com",
                  "address": {"street": "1 Main St", "city": "Paris", "zip": "75001"},
                  "billing": None, "tags": ["a"], "prefs": {}, "display": None, "rev": 1})
    yield c
    client.drop_database("patch_to_set_test")


def load(coll) -> Customer:
    doc = coll.find_one({"_id": 1})
    return Customer.model_validate({k: v for k, v in doc.items() if k != "_id"})


def test_other_address_fields_survive(coll):
    before = load(coll)
    after = before.model_copy(update={"address": Address(street="1 Main St", city="Lyon", zip="75001")})
    assert write_patch(coll, 1, before.rev, patch_to_set(before, after, {"address": {"city": "Lyon"}}))
    assert coll.find_one({"_id": 1})["address"] == {"street": "1 Main St", "city": "Lyon", "zip": "75001"}
    assert coll.find_one({"_id": 1})["rev"] == 2


def test_naive_set_of_the_nested_dict_wipes_the_other_fields(coll):
    # What the bug looked like: $set of the body's nested dict.
    coll.update_one({"_id": 1}, {"$set": {"address": {"city": "Lyon"}}})
    assert coll.find_one({"_id": 1})["address"] == {"city": "Lyon"}


def test_stale_revision_is_a_conflict_and_keeps_the_other_write(coll):
    before = load(coll)
    coll.update_one({"_id": 1}, {"$set": {"email": "new@example.com"}, "$inc": {"rev": 1}})
    after = before.model_copy(update={"name": "Ann Lee"})
    assert not write_patch(coll, 1, before.rev, patch_to_set(before, after, {"name": "Ann Lee"}))
    doc = coll.find_one({"_id": 1})
    assert (doc["name"], doc["email"], doc["rev"]) == ("Ann", "new@example.com", 2)


def test_dotted_path_into_null_is_refused_by_the_server(coll):
    from pymongo.errors import WriteError

    with pytest.raises(WriteError, match="Cannot create field 'city' in element"):
        coll.update_one({"_id": 1}, {"$set": {"billing.city": "Nice"}})


def test_whole_nested_model_into_null_works(coll):
    before = load(coll)
    billing = Address(street="2 Side St", city="Nice", zip="06000")
    after = before.model_copy(update={"billing": billing})
    set_doc = patch_to_set(before, after, {"billing": billing.model_dump()})
    assert write_patch(coll, 1, before.rev, set_doc)
    assert coll.find_one({"_id": 1})["billing"]["city"] == "Nice"


def test_none_is_stored_as_null(coll):
    before = load(coll)
    after = before.model_copy(update={"email": None})
    assert write_patch(coll, 1, before.rev, patch_to_set(before, after, {"email": None}))
    doc = coll.find_one({"_id": 1})
    assert "email" in doc and doc["email"] is None
