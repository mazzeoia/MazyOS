-- Gestor Ads — Fase 3a: Agente conversacional (Telegram + WhatsApp)
-- Applied via Supabase MCP apply_migration on project lwmvswhzrruwttfweidj.

CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    ad_account_id UUID REFERENCES ad_accounts(id) ON DELETE SET NULL,
    channel TEXT NOT NULL CHECK (channel IN ('telegram', 'evolution', 'whatsapp_cloud')),
    channel_user_id TEXT NOT NULL,
    resumo_memoria TEXT NOT NULL DEFAULT '',
    memoria_negocio JSONB NOT NULL DEFAULT '{}',
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (channel, channel_user_id)
);
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
CREATE POLICY "conversations_owner_policy" ON conversations FOR ALL USING (owner_id = auth.uid());

CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    papel TEXT NOT NULL CHECK (papel IN ('user', 'assistant', 'tool')),
    conteudo TEXT NOT NULL DEFAULT '',
    media_url TEXT,
    transcricao TEXT,
    modelo_usado TEXT,
    tokens_input INTEGER NOT NULL DEFAULT 0,
    tokens_output INTEGER NOT NULL DEFAULT 0,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages (conversation_id, criado_em);
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
CREATE POLICY "messages_owner_policy" ON messages FOR ALL USING (
    conversation_id IN (SELECT id FROM conversations WHERE owner_id = auth.uid())
);

-- campaign_drafts already exists (001_initial_schema.sql) — only link it to a conversation.
ALTER TABLE campaign_drafts
    ADD COLUMN IF NOT EXISTS conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL;
