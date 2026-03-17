ALTER TABLE app_dimension_scores
  ADD COLUMN ranking_config_id VARCHAR(50) NULL;

CREATE INDEX idx_app_dim_scores_config
  ON app_dimension_scores (ranking_config_id);

CREATE UNIQUE INDEX uq_app_dim_scores_app_config_dim_period
  ON app_dimension_scores (app_id, ranking_config_id, dimension_id, period_date);
