"""create ranking_config_dimensions join table, migrate data from dimensions_config JSON

Revision ID: 20260601_0007
Revises: 20260601_0006
Create Date: 2026-06-01

Replaces the dimensions_config JSON TEXT column on ranking_configs
with a proper join table (ranking_config_dimensions) that has FK
constraints to both ranking_configs and ranking_dimensions.
"""

import json

from alembic import op
import sqlalchemy as sa


revision = "20260601_0007"
down_revision = "20260601_0006"
branch_labels = None
depends_on = None


def _table_exists(table: str) -> bool:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    return table in inspector.get_table_names()


def _column_exists(table: str, column: str) -> bool:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c["name"] for c in inspector.get_columns(table)]
    return column in cols


def upgrade():
    if _table_exists("ranking_config_dimensions"):
        return

    # 1. Create the join table with explicit charset matching ranking_configs
    op.execute("""
        CREATE TABLE ranking_config_dimensions (
            id INTEGER NOT NULL AUTO_INCREMENT,
            ranking_config_id VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
            dimension_id INTEGER NOT NULL,
            weight FLOAT NOT NULL DEFAULT 1.0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            UNIQUE KEY uq_ranking_config_dimensions (ranking_config_id, dimension_id),
            CONSTRAINT fk_ranking_config_dimensions_config FOREIGN KEY (ranking_config_id)
                REFERENCES ranking_configs (id) ON DELETE CASCADE,
            CONSTRAINT fk_ranking_config_dimensions_dimension FOREIGN KEY (dimension_id)
                REFERENCES ranking_dimensions (id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # 3. Migrate data from JSON column to join table
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, dimensions_config FROM ranking_configs")).fetchall()
    for row in rows:
        config_id = row[0]
        dims_str = row[1] or ""
        try:
            dims = json.loads(dims_str)
        except json.JSONDecodeError:
            dims = []
        if not isinstance(dims, list):
            dims = []
        for item in dims:
            if isinstance(item, dict) and "dim_id" in item:
                conn.execute(
                    sa.text(
                        "INSERT INTO ranking_config_dimensions "
                        "(ranking_config_id, dimension_id, weight) "
                        "VALUES (:config_id, :dim_id, :weight)"
                    ),
                    {
                        "config_id": config_id,
                        "dim_id": item["dim_id"],
                        "weight": item.get("weight", 1.0),
                    },
                )

    # 4. Drop the old JSON column (data is now in the join table)
    if _column_exists("ranking_configs", "dimensions_config"):
        op.drop_column("ranking_configs", "dimensions_config")


def downgrade():
    # 1. Recreate the JSON column
    if not _column_exists("ranking_configs", "dimensions_config"):
        op.add_column("ranking_configs", sa.Column("dimensions_config", sa.Text(), nullable=False, server_default="[]"))

    # 2. Restore data from join table to JSON column
    if _table_exists("ranking_config_dimensions"):
        conn = op.get_bind()
        config_rows = conn.execute(sa.text("SELECT id FROM ranking_configs")).fetchall()
        for (config_id,) in config_rows:
            dim_rows = conn.execute(
                sa.text(
                    "SELECT dimension_id, weight FROM ranking_config_dimensions "
                    "WHERE ranking_config_id = :config_id"
                ),
                {"config_id": config_id},
            ).fetchall()
            dims = [{"dim_id": d[0], "weight": d[1]} for d in dim_rows]
            conn.execute(
                sa.text(
                    "UPDATE ranking_configs SET dimensions_config = :dims "
                    "WHERE id = :config_id"
                ),
                {"dims": json.dumps(dims, ensure_ascii=False), "config_id": config_id},
            )

    # 3. Drop FKs then the join table
    if _table_exists("ranking_config_dimensions"):
        op.drop_constraint("fk_ranking_config_dimensions_config", "ranking_config_dimensions", type_="foreignkey")
        op.drop_constraint("fk_ranking_config_dimensions_dimension", "ranking_config_dimensions", type_="foreignkey")
        op.drop_table("ranking_config_dimensions")
