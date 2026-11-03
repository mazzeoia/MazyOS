"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Download, History, Zap } from "lucide-react";
import { fmt } from "@/lib/formatters";
import { generateAnalysisPdf } from "@/lib/generatePdf";
import type { AnalysisHistoryEntry } from "@/lib/types";

type Props = {
  entries: AnalysisHistoryEntry[];
  loading: boolean;
  accountName: string;
};

export default function AnalysisHistoryPanel({
  entries,
  loading,
  accountName,
}: Props) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  return (
    <div className="panel">
      <div className="panel-head">
        <h3>
          <History
            size={18}
            style={{ marginRight: 8, verticalAlign: "middle" }}
          />
          Histórico de Análises
        </h3>
      </div>

      {loading && entries.length === 0 && (
        <div className="empty-state">
          <p className="muted">Carregando histórico...</p>
        </div>
      )}

      {!loading && entries.length === 0 && (
        <div className="empty-state">
          <p className="muted">
            Nenhuma análise gerada ainda. Clique em &quot;Resumo IA&quot;
            acima para começar.
          </p>
        </div>
      )}

      {entries.length > 0 && (
        <div className="history-list">
          {entries.map((entry) => {
            const isOpen = expandedId === entry.id;
            return (
              <div key={entry.id} className="history-item">
                <button
                  className="history-item-head"
                  onClick={() => setExpandedId(isOpen ? null : entry.id)}
                >
                  <div className="history-item-summary">
                    <span className="history-item-date">
                      {fmt.date(entry.criado_em)}
                    </span>
                    <span className="insight-pill small blue">
                      {entry.kpis.tendencia}
                    </span>
                    <span className="history-item-metric">
                      CPL {fmt.currency(entry.kpis.cpl_medio)}
                    </span>
                    <span className="history-item-metric">
                      {fmt.num(entry.kpis.total_leads)} leads
                    </span>
                  </div>
                  {isOpen ? (
                    <ChevronUp size={18} />
                  ) : (
                    <ChevronDown size={18} />
                  )}
                </button>

                {isOpen && (
                  <div className="history-item-body">
                    <div className="ai-plan-body">
                      {entry.resumo.split("\n").map((p, i) => (
                        <p key={i}>{p}</p>
                      ))}
                    </div>

                    {entry.recomendacoes.length > 0 && (
                      <div style={{ marginTop: 14 }}>
                        <h3 style={{ marginBottom: 10, fontSize: "0.95rem" }}>
                          Recomendações
                        </h3>
                        <div className="command-insight-list">
                          {entry.recomendacoes.map((rec, i) => (
                            <div key={i} className="command-insight green">
                              <span>RECOMENDAÇÃO {i + 1}</span>
                              <p>{rec}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {entry.acoes.length > 0 && (
                      <div style={{ marginTop: 14 }}>
                        <h3 style={{ marginBottom: 10, fontSize: "0.95rem" }}>
                          Ações sugeridas
                        </h3>
                        <div className="ai-plan-action-list">
                          {entry.acoes.map((acao, i) => (
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

                    <button
                      className="ghost-button"
                      style={{ marginTop: 14 }}
                      onClick={() => generateAnalysisPdf(entry, accountName)}
                    >
                      <Download size={16} /> Exportar PDF
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
