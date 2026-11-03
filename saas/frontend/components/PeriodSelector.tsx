"use client";

import { ChevronDown } from "lucide-react";

export const PERIOD_OPTIONS = [
  { value: "today", label: "Hoje" },
  { value: "yesterday", label: "Ontem" },
  { value: "last_7d", label: "Últimos 7 dias" },
  { value: "last_14d", label: "Últimos 14 dias" },
  { value: "last_30d", label: "Últimos 30 dias" },
  { value: "this_month", label: "Este mês" },
] as const;

export type DatePreset = (typeof PERIOD_OPTIONS)[number]["value"];

type Props = {
  value: string;
  onSelect: (preset: string) => void;
};

export default function PeriodSelector({ value, onSelect }: Props) {
  return (
    <div className="select-field period-select">
      <select value={value} onChange={(e) => onSelect(e.target.value)}>
        {PERIOD_OPTIONS.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      <ChevronDown size={14} className="select-chevron" />
    </div>
  );
}
