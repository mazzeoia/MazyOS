-- Gestor Ads — Bloco C: auto-pause automation + notifications
-- Applied via Supabase MCP apply_migration on project lwmvswhzrruwttfweidj.

-- 1. automation_settings — per-account automation config
CREATE TABLE IF NOT EXISTS automation_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    ad_account_id UUID NOT NULL REFERENCES ad_accounts(id) ON DELETE CASCADE,
    owner_email TEXT NOT NULL DEFAULT '',
    auto_pause_enabled BOOLEAN NOT NULL DEFAULT false,
    server_schedule_enabled BOOLEAN NOT NULL DEFAULT false,
    notify_email BOOLEAN NOT NULL DEFAULT true,
    notify_whatsapp BOOLEAN NOT NULL DEFAULT false,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (owner_id, ad_account_id)
);
ALTER TABLE automation_settings ENABLE ROW LEVEL SECURITY;
CREATE POLICY "automation_settings_owner_policy" ON automation_settings FOR ALL USING (owner_id = auth.uid());

-- 2. automation_runs — execution log (manual or cron-triggered)
CREATE TABLE IF NOT EXISTS automation_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    ad_account_id UUID NOT NULL REFERENCES ad_accounts(id) ON DELETE CASCADE,
    trigger TEXT NOT NULL DEFAULT 'manual' CHECK (trigger IN ('manual', 'cron')),
    alerts_found INTEGER NOT NULL DEFAULT 0,
    paused_count INTEGER NOT NULL DEFAULT 0,
    error TEXT,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE automation_runs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "automation_runs_owner_policy" ON automation_runs FOR ALL USING (owner_id = auth.uid());

-- 3. notifications — in-app notification center
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    ad_account_id UUID REFERENCES ad_accounts(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    body TEXT NOT NULL DEFAULT '',
    severity TEXT NOT NULL DEFAULT 'info' CHECK (severity IN ('info', 'warning', 'critical')),
    lida BOOLEAN NOT NULL DEFAULT false,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
CREATE POLICY "notifications_owner_policy" ON notifications FOR ALL USING (owner_id = auth.uid());
CREATE INDEX IF NOT EXISTS idx_notifications_owner_date ON notifications (owner_id, criado_em DESC);
