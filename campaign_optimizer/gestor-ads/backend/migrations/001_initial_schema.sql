-- Gestor Ads — Phase 1 Initial Schema (incremental)
-- Reuses existing tables: meta_connections, ad_accounts, campaigns, campaign_daily_metrics
-- Column mapping vs plan: user_id → owner_id (matches existing schema)
-- Apply via Supabase MCP apply_migration

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. profiles — extends auth.users
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    nome TEXT NOT NULL DEFAULT '',
    telefone_e164 TEXT,
    nivel_tecnico TEXT NOT NULL DEFAULT 'avancado'
        CHECK (nivel_tecnico IN ('leigo', 'avancado')),
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "profiles_user_policy" ON profiles FOR ALL USING (id = auth.uid());

-- 2. campaign_drafts — drafts before sending to Meta
CREATE TABLE IF NOT EXISTS campaign_drafts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    ad_account_id UUID NOT NULL REFERENCES ad_accounts(id) ON DELETE CASCADE,
    payload JSONB NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'rascunho'
        CHECK (status IN ('rascunho', 'aprovado', 'publicando', 'criado', 'erro')),
    meta_campaign_id TEXT,
    erro_detalhes TEXT,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE campaign_drafts ENABLE ROW LEVEL SECURITY;
CREATE POLICY "campaign_drafts_owner_policy" ON campaign_drafts FOR ALL USING (owner_id = auth.uid());

-- 3. creatives — stored images/videos
CREATE TABLE IF NOT EXISTS creatives (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    ad_account_id UUID NOT NULL REFERENCES ad_accounts(id) ON DELETE CASCADE,
    tipo TEXT NOT NULL CHECK (tipo IN ('image', 'video')),
    storage_path TEXT NOT NULL,
    meta_hash TEXT,
    meta_video_id TEXT,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE creatives ENABLE ROW LEVEL SECURITY;
CREATE POLICY "creatives_owner_policy" ON creatives FOR ALL USING (owner_id = auth.uid());

-- 4. audit_log — all Marketing API writes
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    acao TEXT NOT NULL,
    entidade TEXT NOT NULL,
    entidade_id TEXT,
    request JSONB DEFAULT '{}',
    response JSONB DEFAULT '{}',
    origem TEXT NOT NULL DEFAULT 'api',
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
CREATE POLICY "audit_log_owner_policy" ON audit_log FOR ALL USING (owner_id = auth.uid());

-- Trigger: auto-create profile on signup
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO profiles (id, nome)
    VALUES (NEW.id, COALESCE(NEW.raw_user_meta_data->>'nome', ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- =============================================================
-- Existing tables reused (reference only, NOT created here):
-- =============================================================
-- meta_connections  → owner_id, meta_user_id, access_token, scopes, expires_at
-- ad_accounts       → client_id, external_id (act_id), name, currency, timezone
-- campaigns         → client_id, ad_account_id, meta_campaign_id, name, objective, status
-- campaign_daily_metrics → client_id, campaign_id, metric_date, impressions, reach, clicks, etc.
-- meta_ad_accounts  → owner_id, meta_ad_account_id, name, account_status, currency
-- meta_pages        → owner_id, meta_page_id, name, category
