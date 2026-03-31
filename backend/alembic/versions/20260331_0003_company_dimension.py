"""Add company and department dimensions

Revision ID: 20260331_0003
Revises: 20260330_0002
Create Date: 2026-03-31 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260331_0003"
down_revision = "20260330_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    user_columns = {column["name"] for column in inspector.get_columns("users")}
    submission_columns = {column["name"] for column in inspector.get_columns("submissions")}
    app_columns = {column["name"] for column in inspector.get_columns("apps")}

    if "company" not in user_columns:
        op.add_column(
            "users",
            sa.Column("company", sa.String(length=120), nullable=False, server_default=""),
        )
        op.alter_column("users", "company", server_default=None)

    if "company" not in submission_columns:
        op.add_column(
            "submissions",
            sa.Column("company", sa.String(length=120), nullable=False, server_default=""),
        )
    if "department" not in submission_columns:
        op.add_column(
            "submissions",
            sa.Column("department", sa.String(length=120), nullable=False, server_default=""),
        )

    if "company" not in app_columns:
        op.add_column(
            "apps",
            sa.Column("company", sa.String(length=120), nullable=False, server_default=""),
        )
    if "department" not in app_columns:
        op.add_column(
            "apps",
            sa.Column("department", sa.String(length=120), nullable=False, server_default=""),
        )

    op.execute(sa.text("UPDATE submissions SET company = unit_name WHERE company = ''"))
    op.execute(sa.text("UPDATE apps SET company = org WHERE company = ''"))
    op.execute(sa.text("UPDATE submissions SET department = '' WHERE department IS NULL"))
    op.execute(sa.text("UPDATE apps SET department = '' WHERE department IS NULL"))

    if "company" not in submission_columns:
        op.alter_column("submissions", "company", server_default=None)
    if "department" not in submission_columns:
        op.alter_column("submissions", "department", server_default=None)
    if "company" not in app_columns:
        op.alter_column("apps", "company", server_default=None)
    if "department" not in app_columns:
        op.alter_column("apps", "department", server_default=None)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    user_columns = {column["name"] for column in inspector.get_columns("users")}
    submission_columns = {column["name"] for column in inspector.get_columns("submissions")}
    app_columns = {column["name"] for column in inspector.get_columns("apps")}

    if "department" in app_columns:
        op.drop_column("apps", "department")
    if "company" in app_columns:
        op.drop_column("apps", "company")

    if "department" in submission_columns:
        op.drop_column("submissions", "department")
    if "company" in submission_columns:
        op.drop_column("submissions", "company")

    if "company" in user_columns:
        op.drop_column("users", "company")
