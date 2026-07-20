import enum

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class MarketCode(str, enum.Enum):
    CRYPTO = "crypto"
    FOREX = "forex"
    B3 = "b3"


class Market(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "markets"

    code: Mapped[MarketCode] = mapped_column(Enum(MarketCode, name="market_code"), unique=True, nullable=False)
    name_i18n_key: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
