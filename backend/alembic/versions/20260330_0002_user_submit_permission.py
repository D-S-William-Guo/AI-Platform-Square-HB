"""Add can_submit to users

Revision ID: 20260330_0002
Revises: 20260318_0001
Create Date: 2026-03-30 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260330_0002"
down_revision = "20260318_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("users")}

    if "can_submit" not in columns:
        op.add_column(
            "users",
            sa.Column("can_submit", sa.Boolean(), nullable=False, server_default=sa.false()),
        )

    op.execute(
        sa.text(
            "UPDATE users SET can_submit = 1 WHERE username IN ('zhangsan', 'lisi')"
        )
    )

    if "can_submit" not in columns:
        op.alter_column("users", "can_submit", server_default=None)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("users")}
    if "can_submit" in columns:
        op.drop_column("users", "can_submit")
