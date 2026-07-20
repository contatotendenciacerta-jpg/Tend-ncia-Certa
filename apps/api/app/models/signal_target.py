import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.signal import Signal


class SignalTarget(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "signal_targets"

    signal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("signals.id"), nullable=False)
    order: Mapped[int] = mapped_column("order", Integer, nullable=False)
    target_price: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    hit_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    signal: Mapped["Signal"] = relationship(back_populates="targets")
