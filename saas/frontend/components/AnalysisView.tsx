"use client";

import { AlertTriangle, Bot, Download, Sparkles, Target, Zap } from "lucide-react";
import { fmt } from "@/lib/formatters";
import { generateAnalysisPdf } from "@/lib/generatePdf";
import AnalysisHistoryPanel from "./AnalysisHistoryPanel";
import type { AISummary, AnalysisHistoryEntry, RuleAlert } from "@/lib/types";

type Props = {
  selectedAccount: string;
  currentAccountName: string;
  alerts: RuleAlert[];
  aiSummary: AISummary | null;
  evaluating: boolean;
  summarizing: boolean;
  analysisHistory: AnalysisHistoryEntry[];
  loadingHistory: boolean;
  onEvaluate: () => void;
  onSummary: () => void;
  onGoToDashboard: () => void;
};

export default function AnalysisView({
  selectedAccount,
  currentAccountName,
  alerts,
  aiSummary,
  evaluating,
  summarizing,
  analysisHistory,
  loadingHistory,
  onEvaluate,
  onSummary,
  onGoToDashboard,
}: Props) {
  return (
    <>
      <div className="topbar">
        <h1>Análise IA</h1>
      </div>

      {!selectedAccount && (
        <div className="panel">
          <div className="empty-state">
            <p className="muted">
              Conecte uma conta Meta Ads no Dashboard para análise.
            </p>
            <button className="ghost-button" onClick={onGoToDashboard}>
              Ir para Dashboard
            </button>
          </div>
        </div>
      )}

      {selectedAccount && (
        <>
          {/* Action buttons */}
          <div className="hero-panel" style={{ minHeight: "auto" }}>
            <div>
              <p className="eyebrow">{currentAccountName}</p>
              <h2>Inteligência de Performance</h2>
              <p>
                Avalie suas campanhas com regras automáticas e receba um
                resumo inteligente com recomendações de otimização.
              </p>
            </div>
            <div className="hero-actions">
              <button
                className="secondary-button"
                onClick={onEvaluate}
                disabled={evaluating}
              >
                <Target size={16} />{" "}
                {evaluating ? "Avaliando..." : "Avaliar regras"}
              </button>
              <button
                className="secondary-button"
                onClick={onSummary}
                disabled={summarizing}
              >
                <Bot size={16} />{" "}
                {summarizing ? "Gerando..." : "Resumo IA"}
              </button>
              {aiSummary && (
                <button
                  className="secondary-button"
                  onClick={() =>
                    generateAnalysisPdf(aiSummary, currentAccountName)
                  }
                >
                  <Download size={16} /> Exportar PDF
                </button>
              )}
            </div>
          </div>

          {/* Alerts */}
          {alerts.length > 0 && (
            <div className="panel">
              <div className="panel-head">
                <h3>
                  <AlertTriangle
                    size={18}
                    style={{ marginRight: 8, verticalAlign: "middle" }}
                  />
                  {alerts.length} alerta{alerts.length > 1 ? "s" : ""}
                </h3>
              </div>
              <div className="ai-priority-list">
                {alerts.map((alert, i) => (
                  <div
                    key={i}
                    className={`ai-priority ${
                      alert.severity === "alta" || alert.severity === "high"
                        ? "red"
                        : alert.severity === "media" ||
                          alert.severity === "medium"
                        ? "amber"
                        : "blue"
                    }`}
                  >
                    <div>
                      <span>{alert.severity.toUpperCase()}</span>
                      <strong>{alert.rule_name}</strong>
                      <p>{alert.reason}</p>
                    </div>
                    <div>
                      <span>Campanha</span>
                      <strong>{alert.campaign}</strong>
                      <p style={{ marginTop: 8 }}>
                        <strong>Ação:</strong> {alert.action}
                      </p>
                      {alert.should_pause && (
                        <span
                          className="insight-pill red"
                          style={{ marginTop: 8, display: "inline-flex" }}
                        >
                          Sugerir pausa
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {alerts.length === 0 && evaluating && (
            <div className="panel">
              <div className="empty-state">
                <p className="muted">Avaliando regras de performance...</p>
              </div>
            </div>
          )}

          {/* AI Summary */}
          {aiSummary && (
            <>
              {/* KPIs */}
              <div className="metric-grid">
                <div className="metric-card blue">
                  <span>Investimento total</span>
                  <strong>{fmt.currency(aiSummary.kpis.total_spend)}</strong>
                </div>
                <div className="metric-card green">
                  <span>Total de leads</span>
                  <strong>{fmt.num(aiSummary.kpis.total_leads)}</strong>
                </div>
                <div className="metric-card amber">
                  <span>CPL médio</span>
                  <strong>{fmt.currency(aiSummary.kpis.cpl_medio)}</strong>
                </div>
                <div className="metric-card green">
                  <span>CTR médio</span>
                  <strong>{fmt.pct(aiSummary.kpis.ctr_medio)}</strong>
                </div>
              </div>

              {/* Info cards */}
              <div
                className="metric-grid"
                style={{ gridTemplateColumns: "repeat(3, 1fr)" }}
              >
                <div className="metric-card blue">
                  <span>Tendência</span>
                  <strong style={{ fontSize: "1.2rem" }}>
                    {aiSummary.kpis.tendencia}
                  </strong>
                </div>
                <div className="metric-card green">
                  <span>Melhor campanha</span>
                  <strong style={{ fontSize: "1rem" }}>
                    {aiSummary.kpis.melhor_campanha || "—"}
                  </strong>
                </div>
                <div className="metric-card red">
                  <span>Pior campanha</span>
                  <strong style={{ fontSize: "1rem" }}>
                    {aiSummary.kpis.pior_campanha || "—"}
                  </strong>
                </div>
              </div>

              {/* AI analysis panel */}
              <div className="panel ai-panel">
                <div className="panel-head">
                  <h3>
                    <Sparkles
                      size={18}
                      style={{ marginRight: 8, verticalAlign: "middle" }}
                    />
                    Análise Inteligente
                  </h3>
                </div>

                <div className="ai-plan" style={{ marginTop: 18 }}>
                  <div className="ai-plan-head">
                    <div>
                      <span>RESUMO</span>
                      <strong>Visão geral da performance</strong>
                    </div>
                  </div>
                  <div className="ai-plan-body">
                    {aiSummary.resumo.split("\n").map((p, i) => (
                      <p key={i}>{p}</p>
                    ))}
                  </div>
                </div>

                {aiSummary.recomendacoes.length > 0 && (
                  <div style={{ marginTop: 18 }}>
                    <h3 style={{ marginBottom: 12 }}>Recomendações</h3>
                    <div className="command-insight-list">
                      {aiSummary.recomendacoes.map((rec, i) => (
                        <div key={i} className="command-insight green">
                          <span>RECOMENDAÇÃO {i + 1}</span>
                          <p>{rec}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {aiSummary.acoes.length > 0 && (
                  <div style={{ marginTop: 18 }}>
                    <h3 style={{ marginBottom: 12 }}>Ações sugeridas</h3>
                    <div className="ai-plan-action-list">
                      {aiSummary.acoes.map((acao, i) => (
                        <div key={i} className="ai-plan-action-row">
                          <p>
                            <Zap
                              size={14}
                              style={{
                                marginRight: 6,
                                verticalAlign: "middle",
                                color: "var(--flame-2)",
                              }}
                            />
                            {acao.action}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </>
          )}

          {summarizing && (
            <div className="panel">
              <div className="empty-state">
                <p className="muted">
                  <Bot
                    size={18}
                    style={{ marginRight: 6, verticalAlign: "middle" }}
                  />
                  Gerando análise com inteligência artificial...
                </p>
              </div>
            </div>
          )}

          <AnalysisHistoryPanel
            entries={analysisHistory}
            loading={loadingHistory}
            accountName={currentAccountName}
          />
        </>
      )}
    </>
  );
}
