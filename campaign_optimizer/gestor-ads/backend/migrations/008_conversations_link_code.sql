ALTER TABLE conversations
    ADD COLUMN IF NOT EXISTS link_code TEXT,
    ADD COLUMN IF NOT EXISTS link_code_expires_at TIMESTAMPTZ;
