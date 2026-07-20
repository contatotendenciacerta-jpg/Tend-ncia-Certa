"""initial schema

Revision ID: ce5e3572dc55
Revises:
Create Date: 2026-07-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "ce5e3572dc55"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "markets",
        sa.Column("code", sa.Enum("crypto", "forex", "b3", name="market_code"), nullable=False),
        sa.Column("name_i18n_key", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "subscription_tiers",
        sa.Column("code", sa.Enum("basic", "pro", "vip", name="tier_code"), nullable=False),
        sa.Column("name_i18n_key", sa.String(length=255), nullable=False),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("billing_interval", sa.Enum("monthly", "yearly", name="billing_interval"), nullable=False),
        sa.Column("markets_allowed", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("signal_delay_minutes", sa.Integer(), nullable=False),
        sa.Column("max_active_signals_visible", sa.Integer(), nullable=True),
        sa.Column("allows_vip_only_signals", sa.Boolean(), nullable=False),
        sa.Column("push_notifications", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "users",
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("role", sa.Enum("admin", "subscriber", name="user_role"), nullable=False),
        sa.Column("locale", sa.String(length=8), nullable=False),
        sa.Column("status", sa.Enum("active", "suspended", "deleted", name="user_status"), nullable=False),
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "assets",
        sa.Column("market_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["market_id"], ["markets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("market_id", "symbol", name="uq_asset_market_symbol"),
    )

    op.create_table(
        "devices",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("platform", sa.Enum("ios", "android", "web", name="device_platform"), nullable=False),
        sa.Column("push_token", sa.String(length=512), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "subscriptions",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tier_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            sa.Enum("trialing", "active", "past_due", "canceled", "expired", name="subscription_status"),
            nullable=False,
        ),
        sa.Column(
            "payment_provider",
            sa.Enum("stripe", "mercadopago", "pagarme", name="payment_provider"),
            nullable=False,
        ),
        sa.Column("external_subscription_id", sa.String(length=255), nullable=True),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cancel_at_period_end", sa.Boolean(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["tier_id"], ["subscription_tiers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "payments",
        sa.Column("subscription_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column(
            "status",
            sa.Enum("paid", "failed", "refunded", "pending", name="payment_status"),
            nullable=False,
        ),
        sa.Column("provider_reference", sa.String(length=255), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["subscription_id"], ["subscriptions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "signals",
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("direction", sa.Enum("buy", "sell", name="signal_direction"), nullable=False),
        sa.Column("entry_price", sa.Numeric(18, 8), nullable=False),
        sa.Column("stop_loss", sa.Numeric(18, 8), nullable=False),
        sa.Column(
            "timeframe",
            sa.Enum("M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", name="signal_timeframe"),
            nullable=False,
        ),
        sa.Column(
            "confidence_level", sa.Enum("low", "medium", "high", name="confidence_level"), nullable=False
        ),
        sa.Column("source", sa.Enum("manual", "algorithm", name="signal_source"), nullable=False),
        sa.Column("created_by_admin_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("algorithm_name", sa.String(length=255), nullable=True),
        sa.Column(
            "visibility_tier",
            sa.Enum("basic", "pro", "vip", name="signal_visibility_tier"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "pending", "active", "hit_target", "hit_stop", "expired", "canceled", name="signal_status"
            ),
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["created_by_admin_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "signal_targets",
        sa.Column("signal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("target_price", sa.Numeric(18, 8), nullable=False),
        sa.Column("hit_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["signal_id"], ["signals.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("signal_targets")
    op.drop_table("signals")
    op.drop_table("payments")
    op.drop_table("subscriptions")
    op.drop_table("devices")
    op.drop_table("assets")
    op.drop_table("users")
    op.drop_table("subscription_tiers")
    op.drop_table("markets")

    sa.Enum(name="signal_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="signal_visibility_tier").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="signal_source").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="confidence_level").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="signal_timeframe").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="signal_direction").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="payment_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="subscription_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="payment_provider").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="device_platform").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="user_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="user_role").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="billing_interval").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="tier_code").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="market_code").drop(op.get_bind(), checkfirst=True)
