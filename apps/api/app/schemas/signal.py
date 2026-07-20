import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.market import MarketCode
from app.models.signal import (
    ConfidenceLevel,
    SignalDirection,
    SignalSource,
    SignalStatus,
    SignalTimeframe,
    SignalVisibilityTier,
)


class MarketSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: MarketCode
    name_i18n_key: str


class AssetSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    symbol: str
    display_name: str
    market: MarketSummary


class SignalTargetCreate(BaseModel):
    order: int = Field(ge=1)
    target_price: Decimal = Field(gt=0)


class SignalTargetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order: int
    target_price: Decimal
    hit_at: datetime | None


class SignalCreate(BaseModel):
    asset_id: uuid.UUID
    direction: SignalDirection
    entry_price: Decimal = Field(gt=0)
    stop_loss: Decimal = Field(gt=0)
    timeframe: SignalTimeframe
    confidence_level: ConfidenceLevel
    source: SignalSource
    algorithm_name: str | None = Field(default=None, max_length=255)
    visibility_tier: SignalVisibilityTier
    notes: str | None = None
    published_at: datetime | None = None
    targets: list[SignalTargetCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_source_and_targets(self) -> "SignalCreate":
        if self.source == SignalSource.ALGORITHM and not self.algorithm_name:
            raise ValueError("algorithm_name é obrigatório quando source=algorithm")
        if self.source == SignalSource.MANUAL:
            self.algorithm_name = None
        if not self.targets:
            raise ValueError("um sinal precisa de ao menos um alvo (target)")
        return self


class SignalUpdate(BaseModel):
    direction: SignalDirection | None = None
    entry_price: Decimal | None = Field(default=None, gt=0)
    stop_loss: Decimal | None = Field(default=None, gt=0)
    timeframe: SignalTimeframe | None = None
    confidence_level: ConfidenceLevel | None = None
    visibility_tier: SignalVisibilityTier | None = None
    status: SignalStatus | None = None
    notes: str | None = None
    published_at: datetime | None = None
    closed_at: datetime | None = None
    targets: list[SignalTargetCreate] | None = None


class SignalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    asset_id: uuid.UUID
    asset: AssetSummary
    direction: SignalDirection
    entry_price: Decimal
    stop_loss: Decimal
    timeframe: SignalTimeframe
    confidence_level: ConfidenceLevel
    source: SignalSource
    created_by_admin_id: uuid.UUID | None
    algorithm_name: str | None
    visibility_tier: SignalVisibilityTier
    status: SignalStatus
    notes: str | None
    published_at: datetime | None
    closed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    targets: list[SignalTargetRead] = Field(default_factory=list)
