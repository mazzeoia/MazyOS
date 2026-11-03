-- Gestor Ads — Fase 3a fix: conversations.owner_id must stay NULL until a real
-- dashboard user links this chat via the Meta OAuth callback (app/auth/router.py).
-- The chat never auto-provisions an auth.users row.
-- Applied via Supabase MCP apply_migration on project lwmvswhzrruwttfweidj.

ALTER TABLE conversations ALTER COLUMN owner_id DROP NOT NULL;
