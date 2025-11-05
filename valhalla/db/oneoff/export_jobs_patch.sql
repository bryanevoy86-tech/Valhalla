ALTER TABLE export_jobs
  ADD COLUMN IF NOT EXISTS progress INT NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS progress_msg TEXT,
  ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS finished_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_export_jobs_status_created
  ON export_jobs (status, created_at);
