"""remove ranking_type columns, replaced by ranking_config_id

Revision ID: 20260601_0006
Revises: 20260529_0005
Create Date: 2026-06-01

ranking_type was always set to the same value as ranking_config_id.
This migration removes the redundant column from rankings,
historical_rankings, and ranking_audit_logs, and replaces the
historical_rankings index with an equivalent on ranking_config_id.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260601_0006"
down_revision = "20260529_0005"
branch_labels = None
depends_on = None


def _column_exists(table: str, column: str) -> bool:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c["name"] for c in inspector.get_columns(table)]
    return column in cols


def _index_exists(table: str, index: str) -> bool:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    idxs = [i["name"] for i in inspector.get_indexes(table)]
    return index in idxs


def upgrade():
    # 1. Drop the old index on historical_rankings (ranking_type, period_date, run_id)
    if _index_exists("historical_rankings", "idx_historical_rankings_type_period_run"):
        op.drop_index("idx_historical_rankings_type_period_run", table_name="historical_rankings")

    # 2. Drop ranking_type column from rankings
    if _column_exists("rankings", "ranking_type"):
        op.drop_column("rankings", "ranking_type")

    # 3. Drop ranking_type column from historical_rankings
    if _column_exists("historical_rankings", "ranking_type"):
        op.drop_column("historical_rankings", "ranking_type")

    # 4. Drop ranking_type column from ranking_audit_logs
    if _column_exists("ranking_audit_logs", "ranking_type"):
        op.drop_column("ranking_audit_logs", "ranking_type")

    # 5. Create new index on historical_rankings (ranking_config_id, period_date, run_id)
    if not _index_exists("historical_rankings", "idx_historical_rankings_config_period_run"):
        op.create_index(
            "idx_historical_rankings_config_period_run",
            "historical_rankings",
            ["ranking_config_id", "period_date", "run_id"],
        )


def downgrade():
    # Add back ranking_type columns as nullable (data is lost)
    if not _column_exists("rankings", "ranking_type"):
        op.add_column("rankings", sa.Column("ranking_type", sa.String(20), nullable=True))

    if not _column_exists("historical_rankings", "ranking_type"):
        op.add_column("historical_rankings", sa.Column("ranking_type", sa.String(20), nullable=True))

    if not _column_exists("ranking_audit_logs", "ranking_type"):
        op.add_column("ranking_audit_logs", sa.Column("ranking_type", sa.String(50), nullable=True))

    # Recreate old index
    if not _index_exists("historical_rankings", "idx_historical_rankings_type_period_run"):
        op.create_index(
            "idx_historical_rankings_type_period_run",
            "historical_rankings",
            ["ranking_type", "period_date", "run_id"],
        )

    # Drop new index
    if _index_exists("historical_rankings", "idx_historical_rankings_config_period_run"):
        op.drop_index("idx_historical_rankings_config_period_run", table_name="historical_rankings")
