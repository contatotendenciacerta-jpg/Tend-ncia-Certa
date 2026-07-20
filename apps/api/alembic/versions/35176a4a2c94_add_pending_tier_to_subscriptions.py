"""add pending_tier_id to subscriptions

Revision ID: 35176a4a2c94
Revises: ce5e3572dc55
Create Date: 2026-07-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "35176a4a2c94"
down_revision: Union[str, None] = "ce5e3572dc55"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "subscriptions", sa.Column("pending_tier_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        "fk_subscriptions_pending_tier_id_subscription_tiers",
        "subscriptions",
        "subscription_tiers",
        ["pending_tier_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_subscriptions_pending_tier_id_subscription_tiers", "subscriptions", type_="foreignkey"
    )
    op.drop_column("subscriptions", "pending_tier_id")
