import uuid

from pydantic import BaseModel, ConfigDict, Field


class AssetCreate(BaseModel):
    market_id: uuid.UUID
    symbol: str = Field(min_length=1, max_length=32)
    display_name: str = Field(min_length=1, max_length=255)
    is_active: bool = True


class AssetUpdate(BaseModel):
    symbol: str | None = Field(default=None, min_length=1, max_length=32)
    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    is_active: bool | None = None


class AssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    market_id: uuid.UUID
    symbol: str
    display_name: str
    is_active: bool
