-- Add self-service manage token for province submissions

ALTER TABLE submissions
  ADD COLUMN IF NOT EXISTS manage_token VARCHAR(64) DEFAULT '';
