"use client";

import { Play, ShieldAlert } from "lucide-react";
import type { AutomationRunResult, AutomationSettings } from "@/lib/types";

type Props = {
  selectedAccount: string;
  currentAccountName: string;
  settings: AutomationSettings | null;
  loadingSettings: boolean;
  running: boolean;
  lastRunResult: AutomationRunResult | null;
  onUpdateSettings: (patch: Partial<AutomationSettings>) => void;
  onRunNow: () => void;
  onGoToDashboard: () => void;
};

function ToggleRow({
  label,
  description,
  checked,
  onChange,
  disabled,
  danger,
}: {
  label: string;
  description: string;
  checked: boolean;
  onChange: (v: boolean) => void;
  disabled?: boolean;
  danger?: boolean;
}) {
  return (
    <label
      className={`toggle-row${danger ? " danger" : ""}${disabled ? " disabled" : ""}`}
    >
      <input
        type="checkbox"
        checked={checked}
        disabled={disabled}
        onChange={(e) => onChange(e.target.checked)}
      />
      <div className="toggle-row-copy">
        <strong>{label}</strong>
        <span>{description}</span>
      </div>
    </label>
  );
}

export default function AutomationPanel({
  selectedAccount,
  currentAccountName,
  settings,
  loadingSettings,
  running,
  lastRunResult,
  onUpdateSettings,
  onRunNow,
  onGoToDashboard,
}: Props) {
  return (
    <>
      <div className="topbar">
        <h1>Automação</h1>
      </div>

      {!selectedAccount && (
        <div className="panel">
          <div className="empty-state">
            <p className="muted">
              Conecte uma conta Meta Ads no Dashboard para configurar
              automação.
            </p>
            <button className="ghost-button" onClick={onGoToDashboard}>
              Ir para Dashboard
            </button>
          </div>
        </div>
      )}

      {selectedAccount && (
        <>
          <div className="hero-panel" style={{ minHeight: "auto" }}>
            <div>
              <p className="eyebrow">{currentAccountName}</p>
              <h2>Pausa automática de campanhas</h2>
              <p>
                Quando ativado, campanhas que gastam sem gerar lead são
                pausadas automaticamente pela regra &quot;gasto sem
                lead&quot;. Desligado por padrão — você decide quando ligar.
              </p>
            </div>
            <div className="hero-actions">
              <button
                className="secondary-button"
                onClick={onRunNow}
                disabled={running}
              >
                <Play size={16} />{" "}
                {running ? "Rodando..." : "Rodar verificação agora"}
              </button>
            </div>
          </div>

          <div className="panel">
            <div className="panel-head">
              <h3>
                <ShieldAlert
                  size={18}
                  style={{ marginRight: 8, verticalAlign: "middle" }}
                />
                Configurações
              </h3>
            </div>

            {loadingSettings && (
              <div className="empty-state">
                <p className="muted">Carregando configurações...</p>
              </div>
            )}

            {!loadingSettings && (
              <div className="automation-toggle-list">
                <ToggleRow
                  label="Pausar automaticamente"
                  description="Pausa campanhas com gasto sem lead assim que a regra detectar o problema."
                  checked={settings?.auto_pause_enabled ?? false}
                  onChange={(v) => onUpdateSettings({ auto_pause_enabled: v })}
                  danger
                />
                <ToggleRow
                  label="Rodar sozinho no servidor"
                  description="Checa essa conta automaticamente a cada 1 hora, sem precisar clicar em nada."
                  checked={settings?.server_schedule_enabled ?? false}
                  onChange={(v) =>
                    onUpdateSettings({ server_schedule_enabled: v })
                  }
                />
                <ToggleRow
                  label="Notificar por e-mail"
                  description="Manda um e-mail quando encontrar alertas ou pausar alguma campanha."
                  checked={settings?.notify_email ?? true}
                  onChange={(v) => onUpdateSettings({ notify_email: v })}
                />
                <ToggleRow
                  label="Notificar por WhatsApp"
                  description="Em breve — precisa de conta comercial verificada no Meta."
                  checked={false}
                  onChange={() => {}}
                  disabled
                />
              </div>
            )}
          </div>

          {lastRunResult && (
            <div className="panel">
              <div className="panel-head">
                <h3>Última verificação</h3>
              </div>
              <div
                className="metric-grid"
                style={{ gridTemplateColumns: "repeat(2, 1fr)" }}
              >
                <div className="metric-card amber">
                  <span>Alertas encontrados</span>
                  <strong>{lastRunResult.alerts_found}</strong>
                </div>
                <div className="metric-card red">
                  <span>Campanhas pausadas</span>
                  <strong>{lastRunResult.paused_count}</strong>
                </div>
              </div>
              {lastRunResult.errors.length > 0 && (
                <div style={{ marginTop: 14 }}>
                  {lastRunResult.errors.map((err, i) => (
                    <p key={i} className="muted">
                      {err}
                    </p>
                  ))}
                </div>
              )}
            </div>
          )}
        </>
      )}
    </>
  );
}
