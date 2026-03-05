-- 004_add_uniqueness_guards.sql
-- Purpose: add uniqueness guards to prevent duplicate submissions/apps/rankings.
-- IMPORTANT: run backend/scripts/dedupe_data.py --apply before this migration
-- if your database already contains duplicate records.

CREATE UNIQUE INDEX uq_apps_section_name_org
ON apps (section, name, org);

CREATE UNIQUE INDEX uq_submissions_name_unit_status
ON submissions (app_name, unit_name, status);

CREATE UNIQUE INDEX uq_rankings_config_app
ON rankings (ranking_config_id, app_id);
