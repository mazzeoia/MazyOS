"use client";

import { PlugZap, RefreshCw, Sparkles } from "lucide-react";
import { fmt } from "@/lib/formatters";
import type { AdAccount, Campaign, SyncResult } from "@/lib/types";

type Props = {
  accounts: AdAccount[];
  selectedAccount: string;
  setSelectedAccount: (v: string) => void;
  campaigns: Campaign[];
  metaConnected: boolean;
  loadingAccounts: boolean;
  syncing: boolean;
  syncResult: SyncResult | null;
  onRefresh: () => void;
  onMetaConnect: () => void;
  onSync: () => void;
  onGoToAnalysis: () => void;
};

export default function Dashboard({
  accounts,
  selectedAccount,
  setSelectedAccount,
  campaigns,
  metaConnected,
  loadingAccounts,
  syncing,
  syncResult,
  onRefresh,
  onMetaConnect,
  onSync,
  onGoToAnalysis,
}: Props) {
  return (
    <>
      <div className="topbar">
        <h1>Dashboard</h1>
        <div className="topbar-actions">
          <button className="ghost-button" onClick={onRefresh}>
            <RefreshCw size={16} /> Atualizar
          </button>
        </div>
      </div>

      {/* Hero panel */}
      <div className="hero-panel">
        <div>
          <p className="eyebrow">Gestor de Anúncios</p>
          <h2>
            {metaConnected
              ? `${accounts.length} conta${accounts.length > 1 ? "s" : ""} conectada${accounts.length > 1 ? "s" : ""}`
              : "Conecte sua conta Meta"}
          </h2>
          <p>
            {metaConnected
              ? "Suas contas de anúncios estão conectadas. Sincronize campanhas e analise performance."
              : "Conecte sua conta Meta Ads para começar a gerenciar campanhas e receber recomendações de IA."}
          </p>
        </div>
        <div className="hero-actions">
          {!metaConnected ? (
            <button className="secondary-button" onClick={onMetaConnect}>
              <PlugZap size={18} /> Conectar Meta Ads
            </button>
          ) : (
            <>
              <button
                className="secondary-button"
                onClick={onSync}
                disabled={syncing || !selectedAccount}
              >
                <RefreshCw size={16} className={syncing ? "spin" : ""} />{" "}
                {syncing ? "Sincronizando..." : "Sincronizar"}
              </button>
              <button className="secondary-button" onClick={onGoToAnalysis}>
                <Sparkles size={16} /> Analisar com IA
              </button>
            </>
          )}
        </div>
      </div>

      {/* Sync result */}
      {syncResult && (
        <div
          className={`sync-progress ${syncResult.errors.length > 0 ? "error" : "success"}`}
        >
          <div className="sync-progress-head">
            <div>
              <strong>Sincronização concluída</strong>
              <span>
                {syncResult.campaigns_synced} campanhas ·{" "}
                {syncResult.metrics_upserted} métricas
              </span>
            </div>
          </div>
          <div className="progress-track">
            <span style={{ width: "100%" }} />
          </div>
          {syncResult.errors.length > 0 && (
            <small>
              {syncResult.errors.length} erro(s):{" "}
              {syncResult.errors.map((e) => e.campaign).join(", ")}
            </small>
          )}
        </div>
      )}

      {/* Accounts grid */}
      {accounts.length > 0 && (
        <div className="panel">
          <div className="panel-head">
            <h3>Contas de Anúncios</h3>
          </div>
          <div className="asset-list">
            {accounts.map((acc) => (
              <div
                key={acc.id}
                className="asset-row"
                style={{
                  cursor: "pointer",
                  borderLeft:
                    acc.external_id === selectedAccount
                      ? "3px solid var(--flame-2)"
                      : undefined,
                }}
                onClick={() => setSelectedAccount(acc.external_id)}
              >
                <div>
                  <strong>{acc.name || "Sem nome"}</strong>
                  <small>{acc.external_id}</small>
                </div>
                <div style={{ textAlign: "right" }}>
                  <span
                    className={`insight-pill ${acc.status === "active" ? "green" : "amber"}`}
                  >
                    {acc.status || "—"}
                  </span>
                  {acc.currency && (
                    <small style={{ display: "block", marginTop: 4 }}>
                      {acc.currency} · {acc.timezone || "—"}
                    </small>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick campaign summary */}
      {campaigns.length > 0 && (
        <div className="metric-grid">
          <div className="metric-card blue">
            <span>Total campanhas</span>
            <strong>{campaigns.length}</strong>
          </div>
          <div className="metric-card green">
            <span>Ativas</span>
            <strong>
              {campaigns.filter((c) => c.status === "ACTIVE").length}
            </strong>
          </div>
          <div className="metric-card amber">
            <span>Pausadas</span>
            <strong>
              {campaigns.filter((c) => c.status === "PAUSED").length}
            </strong>
          </div>
          <div className="metric-card red">
            <span>Outras</span>
            <strong>
              {
                campaigns.filter(
                  (c) => c.status !== "ACTIVE" && c.status !== "PAUSED"
                ).length
              }
            </strong>
          </div>
        </div>
      )}

      {/* Empty state if not connected */}
      {!metaConnected && !loadingAccounts && (
        <div className="panel">
          <h3>Primeiros passos</h3>
          <div className="step-list">
            <div className="step">
              <span>1</span>
              <div>
                <strong>Conectar Meta Ads</strong>
                <p>
                  Clique em &quot;Conectar Meta Ads&quot; para autorizar o
                  acesso às suas contas de anúncios.
                </p>
              </div>
            </div>
            <div className="step">
              <span>2</span>
              <div>
                <strong>Sincronizar campanhas</strong>
                <p>
                  Após conectar, sincronize para importar campanhas e
                  métricas.
                </p>
              </div>
            </div>
            <div className="step">
              <span>3</span>
              <div>
                <strong>Analisar com IA</strong>
                <p>
                  Use a análise inteligente para receber recomendações de
                  otimização.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
