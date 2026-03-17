-- Add basic auth & RBAC support tables

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(80) NOT NULL,
  chinese_name VARCHAR(80) NOT NULL,
  role VARCHAR(20) DEFAULT 'user',
  phone VARCHAR(30) DEFAULT '',
  email VARCHAR(120) DEFAULT '',
  department VARCHAR(120) DEFAULT '',
  is_active TINYINT(1) DEFAULT 1,
  password_hash VARCHAR(255) NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_users_username (username)
);

CREATE TABLE IF NOT EXISTS auth_sessions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  token_jti VARCHAR(128) NOT NULL,
  issued_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  expires_at DATETIME NOT NULL,
  revoked_at DATETIME DEFAULT NULL,
  ip VARCHAR(80) DEFAULT '',
  user_agent VARCHAR(255) DEFAULT '',
  CONSTRAINT fk_auth_sessions_user FOREIGN KEY (user_id) REFERENCES users(id),
  UNIQUE KEY uq_auth_sessions_token_jti (token_jti),
  KEY idx_auth_sessions_user_id (user_id),
  KEY idx_auth_sessions_expires_at (expires_at)
);

CREATE TABLE IF NOT EXISTS action_logs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  actor_user_id INT DEFAULT NULL,
  actor_role VARCHAR(20) DEFAULT '',
  action VARCHAR(80) NOT NULL,
  resource_type VARCHAR(80) DEFAULT '',
  resource_id VARCHAR(80) DEFAULT '',
  request_id VARCHAR(64) DEFAULT '',
  payload_summary TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_action_logs_actor_user FOREIGN KEY (actor_user_id) REFERENCES users(id),
  KEY idx_action_logs_actor_user_id (actor_user_id),
  KEY idx_action_logs_action (action),
  KEY idx_action_logs_created_at (created_at)
);
