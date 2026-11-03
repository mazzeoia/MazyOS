"use client";

import { CheckCircle2 } from "lucide-react";

type Props = {
  authMode: "login" | "register";
  authEmail: string;
  setAuthEmail: (v: string) => void;
  authPass: string;
  setAuthPass: (v: string) => void;
  authNome: string;
  setAuthNome: (v: string) => void;
  authLoading: boolean;
  authError: string;
  handleAuth: () => void;
  toggleMode: () => void;
};

export default function AuthScreen({
  authMode,
  authEmail,
  setAuthEmail,
  authPass,
  setAuthPass,
  authNome,
  setAuthNome,
  authLoading,
  authError,
  handleAuth,
  toggleMode,
}: Props) {
  return (
    <div className="auth-shell">
      <div className="auth-brand">
        <p className="eyebrow">Creative Agência Marketing</p>
        <h1>Gestor de Anúncios</h1>
        <p className="auth-copy">
          Gerencie suas campanhas Meta Ads com inteligência artificial.
          Sincronize dados, avalie performance e receba recomendações
          automáticas para otimizar seus resultados.
        </p>
        <div className="auth-proof">
          <span>
            <CheckCircle2 size={16} /> Sync Meta Ads
          </span>
          <span>
            <CheckCircle2 size={16} /> Análise com IA
          </span>
          <span>
            <CheckCircle2 size={16} /> Regras automáticas
          </span>
          <span>
            <CheckCircle2 size={16} /> Auditoria completa
          </span>
        </div>
      </div>

      <div className="auth-card">
        <div className="brand-mark small">C</div>
        <h2>{authMode === "login" ? "Entrar" : "Criar conta"}</h2>

        {authMode === "register" && (
          <label>
            Nome
            <input
              type="text"
              placeholder="Seu nome"
              value={authNome}
              onChange={(e) => setAuthNome(e.target.value)}
            />
          </label>
        )}

        <label>
          Email
          <input
            type="email"
            placeholder="seu@email.com"
            value={authEmail}
            onChange={(e) => setAuthEmail(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAuth()}
          />
        </label>

        <label>
          Senha
          <input
            type="password"
            placeholder="••••••••"
            value={authPass}
            onChange={(e) => setAuthPass(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAuth()}
          />
        </label>

        {authError && (
          <p style={{ color: "var(--negative)", margin: 0, fontSize: "0.88rem" }}>
            {authError}
          </p>
        )}

        <button
          className="primary-button"
          onClick={handleAuth}
          disabled={authLoading || !authEmail || !authPass}
        >
          {authLoading
            ? "Aguarde..."
            : authMode === "login"
            ? "Entrar"
            : "Criar conta"}
        </button>

        <button className="link-button" onClick={toggleMode}>
          {authMode === "login"
            ? "Não tem conta? Criar agora"
            : "Já tem conta? Entrar"}
        </button>
      </div>
    </div>
  );
}
