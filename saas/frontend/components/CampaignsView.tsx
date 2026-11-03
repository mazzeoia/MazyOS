"use client";

import { useEffect, useRef, useState } from "react";
import { Pause, Play, RefreshCw } from "lucide-react";
import { fmt } from "@/lib/formatters";
import type { Campaign, SyncResult } from "@/lib/types";

type Props = {
  selectedAccount: string;
  campaigns: Campaign[];
  loadingCampaigns: boolean;
  syncing: boolean;
  syncResult: SyncResult | null;
  actionLoading: string | null;
  onSync: () => void;
  onCampaignAction: (id: string, action: "activate" | "pause") => void;
  onGoToDashboard: () => void;
};

export default function CampaignsView({
  selectedAccount,
  campaigns,
  loadingCampaigns,
  syncing,
  syncResult,
  actionLoading,
  onSync,
  onCampaignAction,
  onGoToDashboard,
}: Props) {
  const [campToPause, setCampToPause] = useState<Campaign | null>(null);
  const lastFocusedRef = useRef<HTMLElement | null>(null);
  const cancelButtonRef = useRef<HTMLButtonElement | null>(null);

  const requestPause = (camp: Campaign, trigger: HTMLElement) => {
    lastFocusedRef.current = trigger;
    setCampToPause(camp);
  };

  const closeConfirm = () => {
    setCampToPause(null);
    lastFocusedRef.current?.focus();
  };

  const confirmPause = () => {
    if (campToPause) onCampaignAction(campToPause.id, "pause");
    closeConfirm();
  };

  useEffect(() => {
    if (!campToPause) return;
    cancelButtonRef.current?.focus();
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") closeConfirm();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [campToPause]);

  return (
    <>
      <div className="topbar">
        <h1>Campanhas</h1>
        <div className="topbar-actions">
          <button
            className="ghost-button"
            onClick={onSync}
            disabled={syncing || !selectedAccount}
          >
            <RefreshCw size={16} />{" "}
            {syncing ? "Sincronizando..." : "Sincronizar Meta"}
          </button>
        </div>
      </div>

      {!selectedAccount && (
        <div className="panel">
          <div className="empty-state">
            <p className="muted">
              Conecte uma conta Meta Ads no Dashboard para visualizar
              campanhas.
            </p>
            <button className="ghost-button" onClick={onGoToDashboard}>
              Ir para Dashboard
            </button>
          </div>
        </div>
      )}

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
        </div>
      )}

      {/* Campaigns table */}
      {selectedAccount && (
        <div className="panel campaigns-panel">
          <div className="panel-head">
            <h3>
              {loadingCampaigns
                ? "Carregando..."
                : `${campaigns.length} campanha${campaigns.length !== 1 ? "s" : ""}`}
            </h3>
          </div>

          {campaigns.length === 0 && !loadingCampaigns && (
            <div className="empty-state">
              <p className="muted">
                Nenhuma campanha encontrada. Sincronize os dados do Meta
                Ads.
              </p>
              <button
                className="ghost-button"
                onClick={onSync}
                disabled={syncing}
              >
                <RefreshCw size={16} /> Sincronizar agora
              </button>
            </div>
          )}

          {campaigns.length > 0 && (
            <div className="campaign-performance-table">
              <div
                className="campaign-performance-row header"
                style={{
                  gridTemplateColumns:
                    "minmax(230px, 1.5fr) 120px 120px 130px 160px",
                  minWidth: 760,
                }}
              >
                <span>Campanha</span>
                <span>Status</span>
                <span>Objetivo</span>
                <span>Orçamento diário</span>
                <span>Ações</span>
              </div>
              {campaigns.map((camp) => (
                <div
                  key={camp.id}
                  className="campaign-performance-row"
                  style={{
                    gridTemplateColumns:
                      "minmax(230px, 1.5fr) 120px 120px 130px 160px",
                    minWidth: 760,
                  }}
                >
                  <div>
                    <strong>{camp.name}</strong>
                    {camp.meta_campaign_id && (
                      <small
                        style={{
                          display: "block",
                          color: "var(--text-dim)",
                          fontSize: "0.78rem",
                        }}
                      >
                        {camp.meta_campaign_id}
                      </small>
                    )}
                  </div>
                  <span>
                    <span
                      className={`insight-pill ${
                        camp.status === "ACTIVE"
                          ? "green"
                          : camp.status === "PAUSED"
                          ? "amber"
                          : "red"
                      }`}
                    >
                      {camp.status}
                    </span>
                  </span>
                  <span>{camp.objective || "—"}</span>
                  <span>
                    {camp.daily_budget
                      ? fmt.currency(camp.daily_budget)
                      : "—"}
                  </span>
                  <div className="row-actions">
                    {camp.status === "PAUSED" && (
                      <button
                        className="ghost-button"
                        disabled={actionLoading === camp.id}
                        onClick={() => onCampaignAction(camp.id, "activate")}
                      >
                        <Play size={14} /> Ativar
                      </button>
                    )}
                    {camp.status === "ACTIVE" && (
                      <button
                        className="ghost-button"
                        disabled={actionLoading === camp.id}
                        onClick={(e) => requestPause(camp, e.currentTarget)}
                      >
                        <Pause size={14} /> Pausar
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Confirmação — pausar campanha para real gasto/veiculação do cliente */}
      {campToPause && (
        <div
          className="confirm-overlay"
          onMouseDown={(e) => {
            if (e.target === e.currentTarget) closeConfirm();
          }}
        >
          <div
            className="confirm-dialog"
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="pause-confirm-title"
            aria-describedby="pause-confirm-desc"
          >
            <h3 id="pause-confirm-title">Pausar campanha?</h3>
            <p id="pause-confirm-desc">
              <strong>{campToPause.name}</strong> para de veicular agora
              {campToPause.daily_budget
                ? ` — o orçamento diário de ${fmt.currency(campToPause.daily_budget)} deixa de ser usado.`
                : "."}
            </p>
            <div className="confirm-dialog-actions">
              <button
                ref={cancelButtonRef}
                className="ghost-button"
                onClick={closeConfirm}
              >
                Cancelar
              </button>
              <button className="primary-button" onClick={confirmPause}>
                <Pause size={14} /> Pausar campanha
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
