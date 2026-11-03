-- Gestor Ads — Bloco B (B2): analysis_history
-- Stores every AI summary generation for a given ad account so users can
-- browse past analyses without re-running the AI.
-- Applied via Supabase MCP apply_migration on project lwmvswhzrruwttfweidj.

CREATE TABLE IF NOT EXISTS analysis_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    ad_account_id UUID NOT NULL REFERENCES ad_accounts(id) ON DELETE CASCADE,
    nivel_tecnico TEXT NOT NULL DEFAULT 'avancado',
    resumo TEXT NOT NULL DEFAULT '',
    recomendacoes JSONB NOT NULL DEFAULT '[]',
    acoes JSONB NOT NULL DEFAULT '[]',
    kpis JSONB NOT NULL DEFAULT '{}',
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE analysis_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY "analysis_history_owner_policy" ON analysis_history FOR ALL USING (owner_id = auth.uid());

-- Fast lookups when listing history for one account, most recent first
CREATE INDEX IF NOT EXISTS idx_analysis_history_account_date
    ON analysis_history (ad_account_id, criado_em DESC);
