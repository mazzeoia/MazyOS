-- Gestor Ads — Fase 3a fix: webhook idempotency. Stores the channel's own
-- message id so a redelivered webhook is skipped instead of reprocessed.
-- Applied via Supabase MCP apply_migration on project lwmvswhzrruwttfweidj.

ALTER TABLE messages ADD COLUMN IF NOT EXISTS external_message_id TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS idx_messages_external_id
    ON messages (conversation_id, external_message_id)
    WHERE external_message_id IS NOT NULL;
