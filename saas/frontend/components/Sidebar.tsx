"use client";

import {
  ClipboardList,
  LayoutDashboard,
  Megaphone,
  PanelLeftClose,
  PanelLeftOpen,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import type { NavSection } from "@/lib/types";

type Props = {
  section: NavSection;
  setSection: (s: NavSection) => void;
  sidebarOpen: boolean;
  setSidebarOpen: (v: boolean) => void;
  userEmail: string;
  onLogout: () => void;
};

const navItems: { key: NavSection; icon: React.ReactNode; label: string }[] = [
  { key: "dashboard", icon: <LayoutDashboard size={20} />, label: "Dashboard" },
  { key: "campaigns", icon: <Megaphone size={20} />, label: "Campanhas" },
  { key: "analysis", icon: <Sparkles size={20} />, label: "Análise IA" },
  { key: "automation", icon: <ShieldAlert size={20} />, label: "Automação" },
  { key: "audit", icon: <ClipboardList size={20} />, label: "Auditoria" },
];

export default function Sidebar({
  section,
  setSection,
  sidebarOpen,
  setSidebarOpen,
  userEmail,
  onLogout,
}: Props) {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-mark small">C</div>
        <div className="sidebar-brand-copy">
          <strong>CREATIVE ADS</strong>
          <span>Gestor de Anúncios</span>
        </div>
        <button
          className="sidebar-toggle"
          onClick={() => setSidebarOpen(!sidebarOpen)}
          aria-label={sidebarOpen ? "Recolher menu" : "Expandir menu"}
          aria-expanded={sidebarOpen}
        >
          {sidebarOpen ? <PanelLeftClose size={18} /> : <PanelLeftOpen size={18} />}
        </button>
      </div>

      <nav className="nav-list">
        {navItems.map((item) => (
          <button
            key={item.key}
            className={`nav-item${section === item.key ? " active" : ""}`}
            onClick={() => setSection(item.key)}
          >
            {item.icon}
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="sidebar-status">
        <ShieldCheck size={18} />
        <div>
          <strong>{userEmail}</strong>
          <span>
            <button
              className="link-button"
              style={{
                color: "inherit",
                fontSize: "0.76rem",
                minHeight: "auto",
                padding: 0,
              }}
              onClick={onLogout}
            >
              Sair
            </button>
          </span>
        </div>
      </div>
    </aside>
  );
}
