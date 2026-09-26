import os

import pytest
from pymongo import MongoClient

from store import save_patch

URI = os.environ.get("MONGODB_URI")
pytestmark = pytest.mark.skipif(not URI, reason="needs MONGODB_URI (a development server)")


@pytest.fixture
def coll():
    c = MongoClient(URI)["patch_test"]["customers"]
    c.drop()
    yield c
    c.drop()


def test_patch_name(coll):
    coll.insert_one({"_id": 1, "name": "Ann", "address": {"street": "1 Main St", "city": "Paris", "zip": "75001"}, "rev": 1})
    save_patch(coll, 1, {"name": "Ann Lee"})
    assert coll.find_one({"_id": 1})["name"] == "Ann Lee"
