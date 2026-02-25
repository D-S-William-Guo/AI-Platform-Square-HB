-- Phase-4 PR-C: ranking audit coverage (MySQL incremental migration)

CREATE TABLE IF NOT EXISTS ranking_audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    action VARCHAR(80) NOT NULL,
    ranking_type VARCHAR(50) NULL,
    ranking_config_id VARCHAR(50) NULL,
    period_date DATE NULL,
    run_id VARCHAR(36) NULL,
    actor VARCHAR(100) NOT NULL DEFAULT 'system',
    payload_summary TEXT NULL,
    created_at DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ranking_audit_logs_created_at (created_at),
    INDEX idx_ranking_audit_logs_config_period (ranking_config_id, period_date),
    INDEX idx_ranking_audit_logs_action (action)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
