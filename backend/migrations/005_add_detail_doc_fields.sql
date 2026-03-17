-- Add dedicated detail document fields for submission/app entities

ALTER TABLE apps
  ADD COLUMN IF NOT EXISTS detail_doc_url VARCHAR(500) DEFAULT '';

ALTER TABLE apps
  ADD COLUMN IF NOT EXISTS detail_doc_name VARCHAR(255) DEFAULT '';

ALTER TABLE submissions
  ADD COLUMN IF NOT EXISTS detail_doc_url VARCHAR(500) DEFAULT '';

ALTER TABLE submissions
  ADD COLUMN IF NOT EXISTS detail_doc_name VARCHAR(255) DEFAULT '';
