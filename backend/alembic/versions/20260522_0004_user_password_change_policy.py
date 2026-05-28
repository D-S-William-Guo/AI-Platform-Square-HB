"""Add local password change policy fields

Revision ID: 20260522_0004
Revises: 20260331_0003
Create Date: 2026-05-22 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260522_0004"
down_revision = "20260331_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    user_columns = {column["name"] for column in inspector.get_columns("users")}

    if "must_change_password" not in user_columns:
        op.add_column(
            "users",
            sa.Column("must_change_password", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        )
        op.alter_column("users", "must_change_password", server_default=None)

    if "password_changed_at" not in user_columns:
        op.add_column(
            "users",
            sa.Column("password_changed_at", sa.DateTime(), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    user_columns = {column["name"] for column in inspector.get_columns("users")}

    if "password_changed_at" in user_columns:
        op.drop_column("users", "password_changed_at")
    if "must_change_password" in user_columns:
        op.drop_column("users", "must_change_password")
