-- Gestor Ads — instrumentação mínima de uso do produto
-- Registra eventos leves (login, troca de conta, sync manual, rodou análise
-- IA, exportou PDF, mexeu em automação, trocou de seção) pra saber o que
-- está sendo usado de verdade, sem depender de docker logs no VPS.
-- Aplicado via Supabase MCP apply_migration no projeto lwmvswhzrruwttfweidj.

CREATE TABLE IF NOT EXISTS product_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    evento TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE product_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY "product_events_owner_policy" ON product_events FOR ALL USING (owner_id = auth.uid());

-- Fast lookups: histórico de um usuário, mais recente primeiro; e contagem
-- por tipo de evento (usado pelo endpoint /events/summary).
CREATE INDEX IF NOT EXISTS idx_product_events_owner_date ON product_events (owner_id, criado_em DESC);
CREATE INDEX IF NOT EXISTS idx_product_events_evento ON product_events (evento);
