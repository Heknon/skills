from datetime import datetime

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class OrderOut(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    order_id: int
    total_cents: int
    placed_at: datetime
