-- Add province submission fields required by approval/detail alignment.
ALTER TABLE submissions
  ADD COLUMN IF NOT EXISTS monthly_calls FLOAT DEFAULT 0.0,
  ADD COLUMN IF NOT EXISTS difficulty VARCHAR(20) DEFAULT 'Medium';

