from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


Status = Literal["created", "picked_up", "in_transit", "out_for_delivery", "delivered", "exception"]


class ShipmentCreate(BaseModel):
    recipient: str = Field(min_length=1, max_length=120)
    destination: str = Field(min_length=1, max_length=200)


class ShipmentStatusUpdate(BaseModel):
    status: Status


class ShipmentView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tracking_number: str
    recipient: str
    destination: str
    status: Status
    created_at: datetime
