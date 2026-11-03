/* ======================================================================
   PDF report generator — exports AI analysis as a branded PDF
   Uses jsPDF + jspdf-autotable (client-side only)
   ====================================================================== */

import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
import { track } from "./track";
import type { AISummary } from "./types";

const COLORS = {
  brand: [232, 93, 4] as [number, number, number], // #e85d04
  dark: [26, 26, 26] as [number, number, number],
  muted: [120, 120, 120] as [number, number, number],
  white: [255, 255, 255] as [number, number, number],
  bg: [245, 245, 245] as [number, number, number],
};

function fmtCurrency(v: number): string {
  return v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function fmtPct(v: number): string {
  return `${v.toFixed(2)}%`;
}

function fmtNum(v: number): string {
  return v.toLocaleString("pt-BR");
}

export function generateAnalysisPdf(
  summary: AISummary,
  accountName: string
): void {
  const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
  const pageWidth = doc.internal.pageSize.getWidth();
  const margin = 18;
  const contentWidth = pageWidth - margin * 2;
  let y = 20;

  /* ---- Header ---- */
  doc.setFillColor(...COLORS.brand);
  doc.rect(0, 0, pageWidth, 36, "F");

  doc.setTextColor(...COLORS.white);
  doc.setFontSize(20);
  doc.setFont("helvetica", "bold");
  doc.text("CREATIVE ADS", margin, 16);

  doc.setFontSize(10);
  doc.setFont("helvetica", "normal");
  doc.text("Relatório de Análise IA", margin, 24);

  doc.setFontSize(9);
  const dateStr = new Date().toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  });
  doc.text(dateStr, pageWidth - margin, 16, { align: "right" });
  doc.text(accountName, pageWidth - margin, 24, { align: "right" });

  y = 46;

  /* ---- KPIs table ---- */
  doc.setTextColor(...COLORS.dark);
  doc.setFontSize(13);
  doc.setFont("helvetica", "bold");
  doc.text("Indicadores de Performance", margin, y);
  y += 4;

  autoTable(doc, {
    startY: y,
    margin: { left: margin, right: margin },
    head: [["Investimento", "Leads", "CPL Médio", "CTR Médio"]],
    body: [
      [
        fmtCurrency(summary.kpis.total_spend),
        fmtNum(summary.kpis.total_leads),
        fmtCurrency(summary.kpis.cpl_medio),
        fmtPct(summary.kpis.ctr_medio),
      ],
    ],
    styles: { fontSize: 10, cellPadding: 4 },
    headStyles: {
      fillColor: COLORS.brand,
      textColor: COLORS.white,
      fontStyle: "bold",
    },
    bodyStyles: { textColor: COLORS.dark },
    theme: "grid",
  });

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  y = (doc as any).lastAutoTable.finalY + 6;

  /* ---- Tendency + best/worst ---- */
  autoTable(doc, {
    startY: y,
    margin: { left: margin, right: margin },
    head: [["Tendência", "Melhor Campanha", "Pior Campanha"]],
    body: [
      [
        summary.kpis.tendencia,
        summary.kpis.melhor_campanha || "—",
        summary.kpis.pior_campanha || "—",
      ],
    ],
    styles: { fontSize: 10, cellPadding: 4 },
    headStyles: {
      fillColor: [60, 60, 60],
      textColor: COLORS.white,
      fontStyle: "bold",
    },
    bodyStyles: { textColor: COLORS.dark },
    theme: "grid",
  });

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  y = (doc as any).lastAutoTable.finalY + 12;

  /* ---- Helper: check page break ---- */
  const pageHeight = doc.internal.pageSize.getHeight();
  const checkPage = (needed: number) => {
    if (y + needed > pageHeight - 20) {
      doc.addPage();
      y = 20;
    }
  };

  /* ---- AI Summary ---- */
  checkPage(30);
  doc.setFontSize(13);
  doc.setFont("helvetica", "bold");
  doc.setTextColor(...COLORS.dark);
  doc.text("Análise Inteligente", margin, y);
  y += 7;

  doc.setFontSize(10);
  doc.setFont("helvetica", "normal");
  doc.setTextColor(...COLORS.dark);

  const resumoLines = doc.splitTextToSize(summary.resumo, contentWidth);
  for (const line of resumoLines) {
    checkPage(6);
    doc.text(line, margin, y);
    y += 5;
  }
  y += 6;

  /* ---- Recommendations ---- */
  if (summary.recomendacoes.length > 0) {
    checkPage(20);
    doc.setFontSize(13);
    doc.setFont("helvetica", "bold");
    doc.setTextColor(...COLORS.brand);
    doc.text("Recomendações", margin, y);
    y += 7;

    doc.setFontSize(10);
    doc.setFont("helvetica", "normal");
    doc.setTextColor(...COLORS.dark);

    summary.recomendacoes.forEach((rec, i) => {
      checkPage(12);
      const label = `${i + 1}. `;
      const recLines = doc.splitTextToSize(rec, contentWidth - 8);
      doc.setFont("helvetica", "bold");
      doc.text(label, margin, y);
      doc.setFont("helvetica", "normal");
      for (const rl of recLines) {
        doc.text(rl, margin + 8, y);
        y += 5;
      }
      y += 2;
    });
    y += 4;
  }

  /* ---- Suggested actions ---- */
  if (summary.acoes.length > 0) {
    checkPage(20);
    doc.setFontSize(13);
    doc.setFont("helvetica", "bold");
    doc.setTextColor(...COLORS.brand);
    doc.text("Ações Sugeridas", margin, y);
    y += 7;

    doc.setFontSize(10);
    doc.setFont("helvetica", "normal");
    doc.setTextColor(...COLORS.dark);

    summary.acoes.forEach((acao) => {
      checkPage(12);
      const acaoLines = doc.splitTextToSize(`⚡ ${acao.action}`, contentWidth);
      for (const al of acaoLines) {
        doc.text(al, margin, y);
        y += 5;
      }
      y += 2;
    });
  }

  /* ---- Footer ---- */
  const totalPages = doc.getNumberOfPages();
  for (let p = 1; p <= totalPages; p++) {
    doc.setPage(p);
    doc.setFontSize(8);
    doc.setTextColor(...COLORS.muted);
    doc.text(
      `Creative Agência Marketing — Gerado automaticamente em ${dateStr}`,
      margin,
      pageHeight - 10
    );
    doc.text(
      `Página ${p} de ${totalPages}`,
      pageWidth - margin,
      pageHeight - 10,
      { align: "right" }
    );
  }

  /* ---- Save ---- */
  const fileName = `relatorio-${accountName.replace(/[^a-zA-Z0-9]/g, "_")}-${new Date().toISOString().slice(0, 10)}.pdf`;
  doc.save(fileName);

  track("pdf_export", { accountName });
}
