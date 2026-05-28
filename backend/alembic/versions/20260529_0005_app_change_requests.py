"""Add app change request workflow

Revision ID: 20260529_0005
Revises: 20260522_0004
Create Date: 2026-05-29 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260529_0005"
down_revision = "20260522_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "app_change_requests" in inspector.get_table_names():
        return

    op.create_table(
        "app_change_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("app_id", sa.Integer(), nullable=False),
        sa.Column("source_submission_id", sa.Integer(), nullable=False),
        sa.Column("submitter_user_id", sa.Integer(), nullable=False),
        sa.Column("reviewer_user_id", sa.Integer(), nullable=True),
        sa.Column("app_name", sa.String(length=120), nullable=False),
        sa.Column("unit_name", sa.String(length=120), nullable=False),
        sa.Column("company", sa.String(length=120), nullable=True, server_default=""),
        sa.Column("department", sa.String(length=120), nullable=True, server_default=""),
        sa.Column("contact", sa.String(length=80), nullable=False),
        sa.Column("contact_phone", sa.String(length=20), nullable=True, server_default=""),
        sa.Column("contact_email", sa.String(length=120), nullable=True, server_default=""),
        sa.Column("category", sa.String(length=30), nullable=False),
        sa.Column("scenario", sa.String(length=500), nullable=False),
        sa.Column("embedded_system", sa.String(length=120), nullable=False),
        sa.Column("problem_statement", sa.String(length=255), nullable=False),
        sa.Column("effectiveness_type", sa.String(length=40), nullable=False),
        sa.Column("effectiveness_metric", sa.String(length=120), nullable=False),
        sa.Column("data_level", sa.String(length=10), nullable=False),
        sa.Column("expected_benefit", sa.String(length=300), nullable=False),
        sa.Column("monthly_calls", sa.Float(), nullable=True, server_default="0"),
        sa.Column("difficulty", sa.String(length=20), nullable=True, server_default="Medium"),
        sa.Column("status", sa.String(length=20), nullable=True, server_default="pending"),
        sa.Column("review_reason", sa.String(length=255), nullable=True, server_default=""),
        sa.Column("cover_image_url", sa.String(length=500), nullable=True, server_default=""),
        sa.Column("detail_doc_url", sa.String(length=500), nullable=True, server_default=""),
        sa.Column("detail_doc_name", sa.String(length=255), nullable=True, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["app_id"], ["apps.id"]),
        sa.ForeignKeyConstraint(["reviewer_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["source_submission_id"], ["submissions.id"]),
        sa.ForeignKeyConstraint(["submitter_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_app_change_requests_app_id", "app_change_requests", ["app_id"])
    op.create_index(
        "ix_app_change_requests_source_submission_id",
        "app_change_requests",
        ["source_submission_id"],
    )
    op.create_index(
        "ix_app_change_requests_submitter_user_id",
        "app_change_requests",
        ["submitter_user_id"],
    )
    op.create_index(
        "ix_app_change_requests_reviewer_user_id",
        "app_change_requests",
        ["reviewer_user_id"],
    )
    op.create_index(
        "idx_app_change_requests_app_status",
        "app_change_requests",
        ["app_id", "status"],
    )
    op.create_index(
        "idx_app_change_requests_submitter_status",
        "app_change_requests",
        ["submitter_user_id", "status"],
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "app_change_requests" not in inspector.get_table_names():
        return

    op.drop_index("idx_app_change_requests_submitter_status", table_name="app_change_requests")
    op.drop_index("idx_app_change_requests_app_status", table_name="app_change_requests")
    op.drop_index("ix_app_change_requests_reviewer_user_id", table_name="app_change_requests")
    op.drop_index("ix_app_change_requests_submitter_user_id", table_name="app_change_requests")
    op.drop_index("ix_app_change_requests_source_submission_id", table_name="app_change_requests")
    op.drop_index("ix_app_change_requests_app_id", table_name="app_change_requests")
    op.drop_table("app_change_requests")
