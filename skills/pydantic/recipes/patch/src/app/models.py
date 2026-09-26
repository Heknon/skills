"""A full model and the partial model for PATCH bodies.

Rules for a model that has a partial (pydantic-partial 0.9 to 0.11.1):
- Every nested model the partial must reach inherits PartialModelMixin.
- A nested model on a field with a default is listed as "<field>.*";
  recursive=True alone does not reach it.
- Every field validator accepts None: the partial passes None for a field
  sent as null. The full model re-checks the merged result anyway.
- Every model validator returns early on the partial (context "partial"):
  there it sees the partial's defaults, not the stored values.
- Validators are idempotent: the merged result is validated again,
  stored values included.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator
from pydantic_partial import PartialModelMixin


class Address(PartialModelMixin, BaseModel):
    model_config = ConfigDict(extra="forbid")

    street: str = Field(min_length=1)
    city: str = Field(min_length=1)
    postcode: str = Field(pattern=r"^[0-9A-Z -]{3,10}$")


class User(PartialModelMixin, BaseModel):
    model_config = ConfigDict(extra="forbid")  # a misspelt key is a 422, not ignored

    name: str = Field(min_length=3, max_length=40)
    email: str | None = None
    status: Literal["active", "suspended"] = "active"
    address: Address
    billing: Address | None = None
    tags: list[str] = []
    min_items: int = Field(default=1, ge=0)
    max_items: int = Field(default=10, ge=0)

    @field_validator("name")
    @classmethod
    def tidy_name(cls, v: str | None) -> str | None:
        if v is None:  # only a partial passes None here
            return v
        return " ".join(v.split())

    @model_validator(mode="after")
    def min_not_above_max(self, info: ValidationInfo) -> "User":
        if info.context and info.context.get("partial"):
            return self  # checked on the merged result instead
        if self.min_items > self.max_items:
            raise ValueError("min_items must not be above max_items")
        return self


# Every required field becomes optional; fields with defaults keep them.
# "billing.*" makes the defaulted nested field partial too.
UserPatch = User.model_as_partial(
    *(name for name in User.model_fields if name != "billing"),
    "billing.*",
    recursive=True,
)
