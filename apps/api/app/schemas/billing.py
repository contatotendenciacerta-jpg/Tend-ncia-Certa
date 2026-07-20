import uuid

from pydantic import BaseModel


class CheckoutRequest(BaseModel):
    tier_id: uuid.UUID
