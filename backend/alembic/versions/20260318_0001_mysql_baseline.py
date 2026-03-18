"""MySQL baseline schema

Revision ID: 20260318_0001
Revises:
Create Date: 2026-03-18 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260318_0001"
down_revision = None
branch_labels = None
depends_on = None


TABLE_ARGS = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("chinese_name", sa.String(length=80), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=False),
        sa.Column("email", sa.String(length=120), nullable=False),
        sa.Column("department", sa.String(length=120), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        **TABLE_ARGS,
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.create_table(
        "ranking_configs",
        sa.Column("id", sa.String(length=50), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("dimensions_config", sa.Text(), nullable=False),
        sa.Column("calculation_method", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        **TABLE_ARGS,
    )

    op.create_table(
        "ranking_dimensions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("calculation_method", sa.Text(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        **TABLE_ARGS,
    )
    op.create_index("ix_ranking_dimensions_name", "ranking_dimensions", ["name"], unique=True)

    op.create_table(
        "submissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("app_name", sa.String(length=120), nullable=False),
        sa.Column("unit_name", sa.String(length=120), nullable=False),
        sa.Column("contact", sa.String(length=80), nullable=False),
        sa.Column("contact_phone", sa.String(length=20), nullable=False),
        sa.Column("contact_email", sa.String(length=120), nullable=False),
        sa.Column("category", sa.String(length=30), nullable=False),
        sa.Column("scenario", sa.String(length=500), nullable=False),
        sa.Column("embedded_system", sa.String(length=120), nullable=False),
        sa.Column("problem_statement", sa.String(length=255), nullable=False),
        sa.Column("effectiveness_type", sa.String(length=40), nullable=False),
        sa.Column("effectiveness_metric", sa.String(length=120), nullable=False),
        sa.Column("data_level", sa.String(length=10), nullable=False),
        sa.Column("expected_benefit", sa.String(length=300), nullable=False),
        sa.Column("monthly_calls", sa.Float(), nullable=False),
        sa.Column("difficulty", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("submitter_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("approved_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("rejected_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("rejected_at", sa.DateTime(), nullable=True),
        sa.Column("rejected_reason", sa.String(length=255), nullable=False),
        sa.Column("manage_token", sa.String(length=64), nullable=False),
        sa.Column("cover_image_id", sa.Integer(), nullable=True),
        sa.Column("cover_image_url", sa.String(length=500), nullable=False),
        sa.Column("detail_doc_url", sa.String(length=500), nullable=False),
        sa.Column("detail_doc_name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("ranking_enabled", sa.Boolean(), nullable=False),
        sa.Column("ranking_weight", sa.Float(), nullable=False),
        sa.Column("ranking_tags", sa.String(length=255), nullable=False),
        sa.Column("ranking_dimensions", sa.String(length=500), nullable=False),
        sa.UniqueConstraint("app_name", "unit_name", "status", name="uq_submissions_name_unit_status"),
        **TABLE_ARGS,
    )
    op.create_index("ix_submissions_submitter_user_id", "submissions", ["submitter_user_id"], unique=False)
    op.create_index("ix_submissions_approved_by_user_id", "submissions", ["approved_by_user_id"], unique=False)
    op.create_index("ix_submissions_rejected_by_user_id", "submissions", ["rejected_by_user_id"], unique=False)

    op.create_table(
        "apps",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("org", sa.String(length=60), nullable=False),
        sa.Column("section", sa.String(length=20), nullable=False),
        sa.Column("category", sa.String(length=30), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("monthly_calls", sa.Float(), nullable=False),
        sa.Column("release_date", sa.Date(), nullable=False),
        sa.Column("api_open", sa.Boolean(), nullable=False),
        sa.Column("difficulty", sa.String(length=20), nullable=False),
        sa.Column("contact_name", sa.String(length=50), nullable=False),
        sa.Column("highlight", sa.String(length=200), nullable=False),
        sa.Column("access_mode", sa.String(length=20), nullable=False),
        sa.Column("access_url", sa.String(length=255), nullable=False),
        sa.Column("detail_doc_url", sa.String(length=500), nullable=False),
        sa.Column("detail_doc_name", sa.String(length=255), nullable=False),
        sa.Column("target_system", sa.String(length=120), nullable=False),
        sa.Column("target_users", sa.String(length=120), nullable=False),
        sa.Column("problem_statement", sa.String(length=255), nullable=False),
        sa.Column("effectiveness_type", sa.String(length=40), nullable=False),
        sa.Column("effectiveness_metric", sa.String(length=120), nullable=False),
        sa.Column("cover_image_url", sa.String(length=500), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_from_submission_id", sa.Integer(), sa.ForeignKey("submissions.id"), nullable=True),
        sa.Column("approved_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("ranking_enabled", sa.Boolean(), nullable=True),
        sa.Column("ranking_weight", sa.Float(), nullable=True),
        sa.Column("ranking_tags", sa.String(length=255), nullable=True),
        sa.Column("last_ranking_update", sa.DateTime(), nullable=True),
        sa.Column("last_month_calls", sa.Float(), nullable=True),
        sa.Column("new_users_count", sa.Integer(), nullable=True),
        sa.Column("search_count", sa.Integer(), nullable=True),
        sa.Column("share_count", sa.Integer(), nullable=True),
        sa.Column("favorite_count", sa.Integer(), nullable=True),
        sa.UniqueConstraint("section", "name", "org", name="uq_apps_section_name_org"),
        **TABLE_ARGS,
    )
    op.create_index("ix_apps_created_by_user_id", "apps", ["created_by_user_id"], unique=False)
    op.create_index("ix_apps_created_from_submission_id", "apps", ["created_from_submission_id"], unique=False)
    op.create_index("ix_apps_approved_by_user_id", "apps", ["approved_by_user_id"], unique=False)

    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("token_jti", sa.String(length=128), nullable=False),
        sa.Column("issued_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("ip", sa.String(length=80), nullable=False),
        sa.Column("user_agent", sa.String(length=255), nullable=False),
        **TABLE_ARGS,
    )
    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"], unique=False)
    op.create_index("ix_auth_sessions_token_jti", "auth_sessions", ["token_jti"], unique=True)
    op.create_index("ix_auth_sessions_expires_at", "auth_sessions", ["expires_at"], unique=False)

    op.create_table(
        "action_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("actor_role", sa.String(length=20), nullable=False),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("resource_type", sa.String(length=80), nullable=False),
        sa.Column("resource_id", sa.String(length=80), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("payload_summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        **TABLE_ARGS,
    )
    op.create_index("ix_action_logs_actor_user_id", "action_logs", ["actor_user_id"], unique=False)
    op.create_index("ix_action_logs_action", "action_logs", ["action"], unique=False)
    op.create_index("ix_action_logs_created_at", "action_logs", ["created_at"], unique=False)

    op.create_table(
        "ranking_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("dimension_id", sa.Integer(), nullable=True),
        sa.Column("dimension_name", sa.String(length=100), nullable=False),
        sa.Column("changes", sa.Text(), nullable=False),
        sa.Column("operator", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        **TABLE_ARGS,
    )

    op.create_table(
        "ranking_audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("ranking_type", sa.String(length=50), nullable=True),
        sa.Column("ranking_config_id", sa.String(length=50), nullable=True),
        sa.Column("period_date", sa.Date(), nullable=True),
        sa.Column("run_id", sa.String(length=36), nullable=True),
        sa.Column("actor", sa.String(length=100), nullable=False),
        sa.Column("payload_summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        **TABLE_ARGS,
    )

    op.create_table(
        "submission_images",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("submission_id", sa.Integer(), sa.ForeignKey("submissions.id"), nullable=False),
        sa.Column("image_url", sa.String(length=500), nullable=False),
        sa.Column("thumbnail_url", sa.String(length=500), nullable=False),
        sa.Column("original_name", sa.String(length=255), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(length=50), nullable=False),
        sa.Column("is_cover", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        **TABLE_ARGS,
    )

    op.create_table(
        "app_dimension_scores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("app_id", sa.Integer(), sa.ForeignKey("apps.id"), nullable=False),
        sa.Column("ranking_config_id", sa.String(length=50), sa.ForeignKey("ranking_configs.id"), nullable=True),
        sa.Column("dimension_id", sa.Integer(), sa.ForeignKey("ranking_dimensions.id"), nullable=False),
        sa.Column("dimension_name", sa.String(length=100), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("calculation_detail", sa.Text(), nullable=False),
        sa.Column("period_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "app_id",
            "ranking_config_id",
            "dimension_id",
            "period_date",
            name="uq_app_dim_scores_app_config_dim_period",
        ),
        **TABLE_ARGS,
    )
    op.create_index(
        "ix_app_dimension_scores_ranking_config_id",
        "app_dimension_scores",
        ["ranking_config_id"],
        unique=False,
    )

    op.create_table(
        "rankings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ranking_config_id", sa.String(length=50), sa.ForeignKey("ranking_configs.id"), nullable=False),
        sa.Column("ranking_type", sa.String(length=20), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("app_id", sa.Integer(), sa.ForeignKey("apps.id"), nullable=False),
        sa.Column("tag", sa.String(length=20), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("likes", sa.Integer(), nullable=True),
        sa.Column("metric_type", sa.String(length=20), nullable=False),
        sa.Column("value_dimension", sa.String(length=40), nullable=False),
        sa.Column("usage_30d", sa.Integer(), nullable=False),
        sa.Column("declared_at", sa.Date(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("ranking_config_id", "app_id", name="uq_rankings_config_app"),
        **TABLE_ARGS,
    )

    op.create_table(
        "historical_rankings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ranking_config_id", sa.String(length=50), sa.ForeignKey("ranking_configs.id"), nullable=False),
        sa.Column("ranking_type", sa.String(length=20), nullable=False),
        sa.Column("period_date", sa.Date(), nullable=False),
        sa.Column("run_id", sa.String(length=36), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("app_id", sa.Integer(), sa.ForeignKey("apps.id"), nullable=False),
        sa.Column("app_name", sa.String(length=120), nullable=False),
        sa.Column("app_org", sa.String(length=60), nullable=False),
        sa.Column("tag", sa.String(length=20), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("metric_type", sa.String(length=20), nullable=False),
        sa.Column("value_dimension", sa.String(length=40), nullable=False),
        sa.Column("usage_30d", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "ranking_config_id",
            "app_id",
            "period_date",
            "run_id",
            name="uq_historical_rankings_period_run_app",
        ),
        **TABLE_ARGS,
    )
    op.create_index(
        "idx_historical_rankings_type_period_run",
        "historical_rankings",
        ["ranking_type", "period_date", "run_id"],
        unique=False,
    )

    op.create_table(
        "app_ranking_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("app_id", sa.Integer(), sa.ForeignKey("apps.id"), nullable=False),
        sa.Column("ranking_config_id", sa.String(length=50), sa.ForeignKey("ranking_configs.id"), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        sa.Column("weight_factor", sa.Float(), nullable=False),
        sa.Column("custom_tags", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        **TABLE_ARGS,
    )


def downgrade() -> None:
    op.drop_table("app_ranking_settings")
    op.drop_index("idx_historical_rankings_type_period_run", table_name="historical_rankings")
    op.drop_table("historical_rankings")
    op.drop_table("rankings")
    op.drop_index("ix_app_dimension_scores_ranking_config_id", table_name="app_dimension_scores")
    op.drop_table("app_dimension_scores")
    op.drop_table("submission_images")
    op.drop_table("ranking_audit_logs")
    op.drop_table("ranking_logs")
    op.drop_index("ix_action_logs_created_at", table_name="action_logs")
    op.drop_index("ix_action_logs_action", table_name="action_logs")
    op.drop_index("ix_action_logs_actor_user_id", table_name="action_logs")
    op.drop_table("action_logs")
    op.drop_index("ix_auth_sessions_expires_at", table_name="auth_sessions")
    op.drop_index("ix_auth_sessions_token_jti", table_name="auth_sessions")
    op.drop_index("ix_auth_sessions_user_id", table_name="auth_sessions")
    op.drop_table("auth_sessions")
    op.drop_index("ix_apps_approved_by_user_id", table_name="apps")
    op.drop_index("ix_apps_created_from_submission_id", table_name="apps")
    op.drop_index("ix_apps_created_by_user_id", table_name="apps")
    op.drop_table("apps")
    op.drop_index("ix_submissions_rejected_by_user_id", table_name="submissions")
    op.drop_index("ix_submissions_approved_by_user_id", table_name="submissions")
    op.drop_index("ix_submissions_submitter_user_id", table_name="submissions")
    op.drop_table("submissions")
    op.drop_index("ix_ranking_dimensions_name", table_name="ranking_dimensions")
    op.drop_table("ranking_dimensions")
    op.drop_table("ranking_configs")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
