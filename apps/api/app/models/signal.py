import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class SignalDirection(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"


class SignalTimeframe(str, enum.Enum):
    M1 = "M1"
    M5 = "M5"
    M15 = "M15"
    M30 = "M30"
    H1 = "H1"
    H4 = "H4"
    D1 = "D1"
    W1 = "W1"


class ConfidenceLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SignalSource(str, enum.Enum):
    MANUAL = "manual"
    ALGORITHM = "algorithm"


class SignalVisibilityTier(str, enum.Enum):
    BASIC = "basic"
    PRO = "pro"
    VIP = "vip"


class SignalStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    HIT_TARGET = "hit_target"
    HIT_STOP = "hit_stop"
    EXPIRED = "expired"
    CANCELED = "canceled"


class Signal(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "signals"

    asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False)
    direction: Mapped[SignalDirection] = mapped_column(Enum(SignalDirection, name="signal_direction"), nullable=False)
    entry_price: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    stop_loss: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    timeframe: Mapped[SignalTimeframe] = mapped_column(Enum(SignalTimeframe, name="signal_timeframe"), nullable=False)
    confidence_level: Mapped[ConfidenceLevel] = mapped_column(
        Enum(ConfidenceLevel, name="confidence_level"), nullable=False
    )
    source: Mapped[SignalSource] = mapped_column(Enum(SignalSource, name="signal_source"), nullable=False)
    created_by_admin_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    algorithm_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    visibility_tier: Mapped[SignalVisibilityTier] = mapped_column(
        Enum(SignalVisibilityTier, name="signal_visibility_tier"), nullable=False
    )
    status: Mapped[SignalStatus] = mapped_column(
        Enum(SignalStatus, name="signal_status"), nullable=False, default=SignalStatus.PENDING
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    asset: Mapped["Asset"] = relationship()
    created_by_admin: Mapped["User | None"] = relationship()
    targets: Mapped[list["SignalTarget"]] = relationship(back_populates="signal", cascade="all, delete-orphan")
