-- Initial schema for AI App Square (MySQL 8+)

CREATE TABLE IF NOT EXISTS apps (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  org VARCHAR(60) NOT NULL,
  section VARCHAR(20) NOT NULL,
  category VARCHAR(30) NOT NULL,
  description TEXT NOT NULL,
  status VARCHAR(20) NOT NULL,
  monthly_calls FLOAT NOT NULL,
  release_date DATE NOT NULL,
  api_open TINYINT(1) DEFAULT 0,
  difficulty VARCHAR(20) DEFAULT 'Low',
  contact_name VARCHAR(50) DEFAULT '',
  highlight VARCHAR(200) DEFAULT '',
  access_mode VARCHAR(20) DEFAULT 'direct',
  access_url VARCHAR(255) DEFAULT '',
  target_system VARCHAR(120) DEFAULT '',
  target_users VARCHAR(120) DEFAULT '',
  problem_statement VARCHAR(255) DEFAULT '',
  effectiveness_type VARCHAR(40) DEFAULT 'cost_reduction',
  effectiveness_metric VARCHAR(120) DEFAULT '',
  cover_image_url VARCHAR(500) DEFAULT '',
  ranking_enabled TINYINT(1) DEFAULT 1,
  ranking_weight FLOAT DEFAULT 1.0,
  ranking_tags VARCHAR(255) DEFAULT '',
  last_ranking_update DATETIME DEFAULT NULL,
  last_month_calls FLOAT DEFAULT 0.0,
  new_users_count INT DEFAULT 0,
  search_count INT DEFAULT 0,
  share_count INT DEFAULT 0,
  favorite_count INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS rankings (
  id INT AUTO_INCREMENT PRIMARY KEY,
  ranking_config_id VARCHAR(50) NOT NULL,
  ranking_type VARCHAR(20) NOT NULL,
  position INT NOT NULL,
  app_id INT NOT NULL,
  tag VARCHAR(20) DEFAULT '推荐',
  score INT DEFAULT 0,
  likes INT DEFAULT NULL,
  metric_type VARCHAR(20) DEFAULT 'composite',
  value_dimension VARCHAR(40) DEFAULT 'cost_reduction',
  usage_30d INT DEFAULT 0,
  declared_at DATE NOT NULL,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_rankings_app FOREIGN KEY (app_id) REFERENCES apps(id),
  CONSTRAINT fk_rankings_config FOREIGN KEY (ranking_config_id) REFERENCES ranking_configs(id)
);

CREATE TABLE IF NOT EXISTS submissions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  app_name VARCHAR(120) NOT NULL,
  unit_name VARCHAR(120) NOT NULL,
  contact VARCHAR(80) NOT NULL,
  contact_phone VARCHAR(20) DEFAULT '',
  contact_email VARCHAR(120) DEFAULT '',
  category VARCHAR(30) NOT NULL,
  scenario VARCHAR(500) NOT NULL,
  embedded_system VARCHAR(120) NOT NULL,
  problem_statement VARCHAR(255) NOT NULL,
  effectiveness_type VARCHAR(40) NOT NULL,
  effectiveness_metric VARCHAR(120) NOT NULL,
  data_level VARCHAR(10) NOT NULL,
  expected_benefit VARCHAR(300) NOT NULL,
  status VARCHAR(20) DEFAULT 'pending',
  cover_image_id INT DEFAULT NULL,
  cover_image_url VARCHAR(500) DEFAULT '',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  ranking_enabled TINYINT(1) DEFAULT 1,
  ranking_weight FLOAT DEFAULT 1.0,
  ranking_tags VARCHAR(255) DEFAULT '',
  ranking_dimensions VARCHAR(500) DEFAULT ''
);

CREATE TABLE IF NOT EXISTS submission_images (
  id INT AUTO_INCREMENT PRIMARY KEY,
  submission_id INT NOT NULL,
  image_url VARCHAR(500) NOT NULL,
  thumbnail_url VARCHAR(500) DEFAULT '',
  original_name VARCHAR(255) DEFAULT '',
  file_size INT DEFAULT 0,
  mime_type VARCHAR(50) DEFAULT '',
  is_cover TINYINT(1) DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_submission_images_submission FOREIGN KEY (submission_id) REFERENCES submissions(id)
);

CREATE TABLE IF NOT EXISTS ranking_dimensions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  description TEXT NOT NULL,
  calculation_method TEXT NOT NULL,
  weight FLOAT NOT NULL DEFAULT 1.0,
  is_active TINYINT(1) DEFAULT 1,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ranking_logs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  action VARCHAR(50) NOT NULL,
  dimension_id INT DEFAULT NULL,
  dimension_name VARCHAR(100) NOT NULL,
  changes TEXT NOT NULL,
  operator VARCHAR(100) DEFAULT 'system',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_ranking_logs_dimension FOREIGN KEY (dimension_id) REFERENCES ranking_dimensions(id)
);

-- 榜单配置表
CREATE TABLE IF NOT EXISTS ranking_configs (
  id VARCHAR(50) PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  description TEXT DEFAULT '',
  dimensions_config TEXT DEFAULT '[]',
  calculation_method VARCHAR(50) DEFAULT 'composite',
  is_active TINYINT(1) DEFAULT 1,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 应用维度评分表
CREATE TABLE IF NOT EXISTS app_dimension_scores (
  id INT AUTO_INCREMENT PRIMARY KEY,
  app_id INT NOT NULL,
  dimension_id INT NOT NULL,
  dimension_name VARCHAR(100) NOT NULL,
  score INT DEFAULT 0,
  weight FLOAT DEFAULT 1.0,
  calculation_detail TEXT DEFAULT '',
  period_date DATE NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_app_dim_scores_app FOREIGN KEY (app_id) REFERENCES apps(id),
  CONSTRAINT fk_app_dim_scores_dim FOREIGN KEY (dimension_id) REFERENCES ranking_dimensions(id)
);

-- 历史榜单表
CREATE TABLE IF NOT EXISTS historical_rankings (
  id INT AUTO_INCREMENT PRIMARY KEY,
  ranking_config_id VARCHAR(50) NOT NULL,
  ranking_type VARCHAR(20) NOT NULL,
  period_date DATE NOT NULL,
  position INT NOT NULL,
  app_id INT NOT NULL,
  app_name VARCHAR(120) NOT NULL,
  app_org VARCHAR(60) NOT NULL,
  tag VARCHAR(20) DEFAULT '推荐',
  score INT DEFAULT 0,
  metric_type VARCHAR(20) DEFAULT 'composite',
  value_dimension VARCHAR(40) DEFAULT 'cost_reduction',
  usage_30d INT DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_historical_rankings_app FOREIGN KEY (app_id) REFERENCES apps(id),
  CONSTRAINT fk_historical_rankings_config FOREIGN KEY (ranking_config_id) REFERENCES ranking_configs(id)
);

-- 应用榜单设置表
CREATE TABLE IF NOT EXISTS app_ranking_settings (
  id INT AUTO_INCREMENT PRIMARY KEY,
  app_id INT NOT NULL,
  ranking_config_id VARCHAR(50) DEFAULT NULL,
  is_enabled TINYINT(1) DEFAULT 0,
  weight_factor FLOAT DEFAULT 1.0,
  custom_tags VARCHAR(255) DEFAULT '',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_app_ranking_settings_app FOREIGN KEY (app_id) REFERENCES apps(id),
  CONSTRAINT fk_app_ranking_settings_config FOREIGN KEY (ranking_config_id) REFERENCES ranking_configs(id)
);

-- 添加索引优化查询性能
CREATE INDEX idx_apps_section ON apps(section);
CREATE INDEX idx_apps_status ON apps(status);
CREATE INDEX idx_apps_category ON apps(category);
CREATE INDEX idx_rankings_type ON rankings(ranking_type);
CREATE INDEX idx_rankings_app_id ON rankings(app_id);
CREATE INDEX idx_submissions_status ON submissions(status);
CREATE INDEX idx_historical_rankings_date ON historical_rankings(period_date);
CREATE INDEX idx_historical_rankings_type ON historical_rankings(ranking_type);
CREATE INDEX idx_app_dim_scores_app ON app_dimension_scores(app_id);
CREATE INDEX idx_app_dim_scores_date ON app_dimension_scores(period_date);
CREATE UNIQUE INDEX idx_ranking_dimensions_name ON ranking_dimensions(name);
