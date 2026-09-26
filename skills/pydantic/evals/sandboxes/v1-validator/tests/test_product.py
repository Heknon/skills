import pytest
from pydantic import ValidationError

from catalogue.models import Product


def test_product():
    p = Product(sku="AB-1", name=" Lamp ", price_cents=1999)
    assert p.name == "Lamp"


def test_blank_name_rejected():
    with pytest.raises(ValidationError):
        Product(sku="AB-1", name="  ", price_cents=1)
