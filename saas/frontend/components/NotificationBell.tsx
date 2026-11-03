"use client";

import { useEffect, useRef, useState } from "react";
import { Bell } from "lucide-react";
import { fmt } from "@/lib/formatters";
import type { NotificationEntry } from "@/lib/types";

type Props = {
  notifications: NotificationEntry[];
  onMarkRead: (id: string) => void;
  onMarkAllRead: () => void;
};

export default function NotificationBell({
  notifications,
  onMarkRead,
  onMarkAllRead,
}: Props) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const unread = notifications.filter((n) => !n.lida).length;

  useEffect(() => {
    if (!open) return;
    const onClickOutside = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [open]);

  return (
    <div className="notification-bell" ref={rootRef}>
      <button
        className="notification-bell-trigger"
        onClick={() => setOpen((v) => !v)}
        aria-label="Notificações"
      >
        <Bell size={18} />
        {unread > 0 && (
          <span className="notification-badge">
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </button>

      {open && (
        <div className="notification-dropdown">
          <div className="notification-dropdown-head">
            <strong>Notificações</strong>
            {unread > 0 && (
              <button
                className="link-button"
                style={{ fontSize: "0.76rem", minHeight: "auto", padding: 0 }}
                onClick={onMarkAllRead}
              >
                Marcar todas como lidas
              </button>
            )}
          </div>

          {notifications.length === 0 && (
            <p className="muted" style={{ padding: "16px" }}>
              Nenhuma notificação ainda.
            </p>
          )}

          <div className="notification-list">
            {notifications.map((n) => (
              <button
                key={n.id}
                className={`notification-item ${n.severity}${n.lida ? "" : " unread"}`}
                onClick={() => !n.lida && onMarkRead(n.id)}
              >
                <strong>{n.title}</strong>
                <p>{n.body}</p>
                <span>{fmt.date(n.criado_em)}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
