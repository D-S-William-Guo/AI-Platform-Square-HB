-- Add user traceability fields for submission -> approval -> app lifecycle

ALTER TABLE submissions
  ADD COLUMN IF NOT EXISTS submitter_user_id INT NULL,
  ADD COLUMN IF NOT EXISTS approved_by_user_id INT NULL,
  ADD COLUMN IF NOT EXISTS approved_at DATETIME NULL,
  ADD COLUMN IF NOT EXISTS rejected_by_user_id INT NULL,
  ADD COLUMN IF NOT EXISTS rejected_at DATETIME NULL,
  ADD COLUMN IF NOT EXISTS rejected_reason VARCHAR(255) DEFAULT '',
  ADD COLUMN IF NOT EXISTS updated_at DATETIME NULL;

ALTER TABLE apps
  ADD COLUMN IF NOT EXISTS created_by_user_id INT NULL,
  ADD COLUMN IF NOT EXISTS created_from_submission_id INT NULL,
  ADD COLUMN IF NOT EXISTS approved_by_user_id INT NULL,
  ADD COLUMN IF NOT EXISTS approved_at DATETIME NULL;
