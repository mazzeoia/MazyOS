"use client";

import { RefreshCw } from "lucide-react";
import { fmt } from "@/lib/formatters";
import type { AuditEntry } from "@/lib/types";

type Props = {
  auditLog: AuditEntry[];
  loadingAudit: boolean;
  onRefresh: () => void;
};

export default function AuditView({ auditLog, loadingAudit, onRefresh }: Props) {
  return (
    <>
      <div className="topbar">
        <h1>Auditoria</h1>
        <div className="topbar-actions">
          <button
            className="ghost-button"
            onClick={onRefresh}
            disabled={loadingAudit}
          >
            <RefreshCw size={16} /> Atualizar
          </button>
        </div>
      </div>

      <div className="panel table-panel">
        <div className="panel-head">
          <h3>
            {loadingAudit
              ? "Carregando..."
              : `${auditLog.length} registro${auditLog.length !== 1 ? "s" : ""}`}
          </h3>
        </div>

        {auditLog.length === 0 && !loadingAudit && (
          <div className="empty-state">
            <p className="muted">Nenhum registro de auditoria encontrado.</p>
          </div>
        )}

        {auditLog.length > 0 && (
          <div className="data-table">
            <div
              className="data-row header"
              style={{
                gridTemplateColumns:
                  "minmax(140px, 0.8fr) minmax(120px, 0.6fr) minmax(180px, 1fr) minmax(180px, 1fr)",
              }}
            >
              <span>Data</span>
              <span>Ação</span>
              <span>Entidade</span>
              <span>ID</span>
            </div>
            {auditLog.map((entry) => (
              <div
                key={entry.id}
                className="data-row"
                style={{
                  gridTemplateColumns:
                    "minmax(140px, 0.8fr) minmax(120px, 0.6fr) minmax(180px, 1fr) minmax(180px, 1fr)",
                }}
              >
                <span>{fmt.date(entry.criado_em)}</span>
                <strong>{entry.acao}</strong>
                <span>{entry.entidade}</span>
                <span
                  style={{
                    fontSize: "0.78rem",
                    fontFamily: "monospace",
                  }}
                >
                  {entry.entidade_id || "—"}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
