import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.market import MarketCode


class MarketCreate(BaseModel):
    code: MarketCode
    name_i18n_key: str = Field(min_length=1, max_length=255)
    is_active: bool = True


class MarketUpdate(BaseModel):
    name_i18n_key: str | None = Field(default=None, min_length=1, max_length=255)
    is_active: bool | None = None


class MarketRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: MarketCode
    name_i18n_key: str
    is_active: bool
