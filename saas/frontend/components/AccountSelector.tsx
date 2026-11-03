"use client";

import { ChevronDown } from "lucide-react";
import type { AdAccount } from "@/lib/types";

type Props = {
  accounts: AdAccount[];
  selectedAccount: string;
  onSelect: (externalId: string) => void;
};

export default function AccountSelector({
  accounts,
  selectedAccount,
  onSelect,
}: Props) {
  if (accounts.length === 0) return null;

  const current = accounts.find((a) => a.external_id === selectedAccount);

  return (
    <>
      <div className="select-field account-select">
        <select
          value={selectedAccount}
          onChange={(e) => onSelect(e.target.value)}
        >
          {accounts.map((a) => (
            <option key={a.external_id} value={a.external_id}>
              {a.name || a.external_id}
            </option>
          ))}
        </select>
        <ChevronDown size={14} className="select-chevron" />
      </div>
      {current && (
        <div className="account-selector-meta">
          <span
            className={`insight-pill small ${current.status === "active" ? "green" : "amber"}`}
          >
            {current.status || "—"}
          </span>
          {current.currency && (
            <span className="account-selector-detail">
              {current.currency}
            </span>
          )}
          {accounts.length > 1 && (
            <span className="account-selector-detail">
              {accounts.length} contas
            </span>
          )}
        </div>
      )}
    </>
  );
}
