-- Phase-4 PR-B: add run_id publish marker for historical_rankings
ALTER TABLE historical_rankings
  ADD COLUMN run_id VARCHAR(36) NULL COMMENT '发布批次ID，同一天多次发布的区分键' AFTER period_date;

ALTER TABLE historical_rankings
  ADD UNIQUE KEY uq_historical_rankings_period_run_app (ranking_config_id, app_id, period_date, run_id);

ALTER TABLE historical_rankings
  ADD KEY idx_historical_rankings_type_period_run (ranking_type, period_date, run_id);
