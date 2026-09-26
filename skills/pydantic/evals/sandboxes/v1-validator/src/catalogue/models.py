from pydantic import BaseModel, ConfigDict, validator


class Product(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    sku: str
    name: str
    price_cents: int

    @validator("name")
    def name_not_blank(cls, v):
        if not v:
            raise ValueError("name must not be blank")
        return v
