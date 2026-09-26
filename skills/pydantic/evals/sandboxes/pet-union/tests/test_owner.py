from pets.models import Cat, Dog, Owner


def test_dog():
    o = Owner.model_validate({"name": "Ann", "pets": [{"type": "dog", "name": "Rex", "breed": "collie"}]})
    assert isinstance(o.pets[0], Dog)


def test_cat_with_indoor():
    o = Owner.model_validate({"name": "Ann", "pets": [{"type": "cat", "name": "Tom", "indoor": False}]})
    assert isinstance(o.pets[0], Cat)
