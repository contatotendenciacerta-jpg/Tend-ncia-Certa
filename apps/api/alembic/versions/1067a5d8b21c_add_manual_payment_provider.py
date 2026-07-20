"""add manual value to payment_provider enum

Revision ID: 1067a5d8b21c
Revises: 35176a4a2c94
Create Date: 2026-07-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1067a5d8b21c"
down_revision: Union[str, None] = "35176a4a2c94"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Lets admins grant a subscription for testing without a real payment
    # (see POST /admin/users/{id}/grant-subscription). Postgres 12+ allows
    # ALTER TYPE ... ADD VALUE inside a transaction as long as the new
    # value isn't used in that same transaction, which this migration
    # doesn't do.
    op.execute("ALTER TYPE payment_provider ADD VALUE IF NOT EXISTS 'manual'")


def downgrade() -> None:
    # Removing a value from a Postgres enum requires recreating the type
    # and remapping every column that uses it - not worth automating for
    # an additive, backward-compatible change. Roll back manually if ever
    # needed.
    pass
