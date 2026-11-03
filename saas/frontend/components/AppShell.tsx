"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { apiFetch } from "@/lib/api";
import { track } from "@/lib/track";
import type {
  AdAccount,
  AISummary,
  AnalysisHistoryEntry,
  AuditEntry,
  AutomationRunResult,
  AutomationSettings,
  Campaign,
  NavSection,
  NotificationEntry,
  RuleAlert,
  SyncResult,
} from "@/lib/types";

import Sidebar from "./Sidebar";
import AccountSelector from "./AccountSelector";
import PeriodSelector from "./PeriodSelector";
import NotificationBell from "./NotificationBell";
import Dashboard from "./Dashboard";
import CampaignsView from "./CampaignsView";
import AnalysisView from "./AnalysisView";
import AutomationPanel from "./AutomationPanel";
import AuditView from "./AuditView";

const LS_KEY = "gestor-ads:selected-account";
const LS_KEY_PERIOD = "gestor-ads:selected-period";
const DEFAULT_PERIOD = "last_7d";

type Props = {
  userEmail: string;
  onLogout: () => void;
};

export default function AppShell({ userEmail, onLogout }: Props) {
  const [section, setSection] = useState<NavSection>("dashboard");
  const [sidebarOpen, setSidebarOpen] = useState(true);

  /* ---- data state ---- */
  const [accounts, setAccounts] = useState<AdAccount[]>([]);
  const [selectedAccount, setSelectedAccount] = useState<string>("");
  const [selectedPeriod, setSelectedPeriod] = useState<string>(DEFAULT_PERIOD);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [alerts, setAlerts] = useState<RuleAlert[]>([]);
  const [aiSummary, setAiSummary] = useState<AISummary | null>(null);
  const [auditLog, setAuditLog] = useState<AuditEntry[]>([]);
  const [analysisHistory, setAnalysisHistory] = useState<AnalysisHistoryEntry[]>([]);
  const [automationSettings, setAutomationSettings] = useState<AutomationSettings | null>(null);
  const [lastAutomationRun, setLastAutomationRun] = useState<AutomationRunResult | null>(null);
  const [notifications, setNotifications] = useState<NotificationEntry[]>([]);
  const [metaConnected, setMetaConnected] = useState(false);

  /* ---- loading flags ---- */
  const [loadingAccounts, setLoadingAccounts] = useState(false);
  const [loadingCampaigns, setLoadingCampaigns] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState<SyncResult | null>(null);
  const [evaluating, setEvaluating] = useState(false);
  const [summarizing, setSummarizing] = useState(false);
  const [loadingAudit, setLoadingAudit] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [loadingAutomationSettings, setLoadingAutomationSettings] = useState(false);
  const [automationRunning, setAutomationRunning] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const mountedRef = useRef(true);
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  /* ---- persist selected account ---- */
  const selectAccount = useCallback((externalId: string) => {
    setSelectedAccount(externalId);
    track("account_switch", { act_id: externalId });
    try {
      localStorage.setItem(LS_KEY, externalId);
    } catch {
      /* storage full or blocked */
    }
  }, []);

  /* ---- qual seção está sendo usada de verdade ---- */
  useEffect(() => {
    track("section_view", { section });
  }, [section]);

  /* ---- persist selected period ---- */
  const selectPeriod = useCallback((preset: string) => {
    setSelectedPeriod(preset);
    try {
      localStorage.setItem(LS_KEY_PERIOD, preset);
    } catch {
      /* storage full or blocked */
    }
  }, []);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(LS_KEY_PERIOD);
      if (stored) setSelectedPeriod(stored);
    } catch {
      /* blocked */
    }
  }, []);

  /* ---- load accounts ---- */
  const loadAccounts = useCallback(async () => {
    setLoadingAccounts(true);
    try {
      const data = await apiFetch<AdAccount[]>("/accounts");
      if (!mountedRef.current) return;
      setAccounts(data);
      setMetaConnected(data.length > 0);
      if (data.length > 0 && !selectedAccount) {
        let restored = "";
        try {
          restored = localStorage.getItem(LS_KEY) || "";
        } catch {
          /* blocked */
        }
        const match = data.find((a) => a.external_id === restored);
        const pick = match ? restored : data[0].external_id;
        setSelectedAccount(pick);
        try {
          localStorage.setItem(LS_KEY, pick);
        } catch {
          /* silent */
        }
      }
    } catch {
      /* silent */
    } finally {
      if (mountedRef.current) setLoadingAccounts(false);
    }
  }, [selectedAccount]);

  useEffect(() => {
    loadAccounts();
  }, [loadAccounts]);

  /* ---- load campaigns when account selected ---- */
  const loadCampaigns = useCallback(async () => {
    if (!selectedAccount) return;
    setLoadingCampaigns(true);
    setCampaigns([]);
    try {
      const data = await apiFetch<Campaign[]>(
        `/campaigns?act_id=${selectedAccount}`
      );
      if (mountedRef.current) setCampaigns(data);
    } catch {
      /* silent */
    } finally {
      if (mountedRef.current) setLoadingCampaigns(false);
    }
  }, [selectedAccount]);

  useEffect(() => {
    if (selectedAccount) loadCampaigns();
  }, [selectedAccount, loadCampaigns]);

  /* ---- Meta OAuth ---- */
  const handleMetaConnect = useCallback(async () => {
    try {
      const data = await apiFetch<{ url: string }>("/auth/meta/login");
      window.open(data.url, "_blank", "noopener");
    } catch (err) {
      alert(err instanceof Error ? err.message : "Erro ao conectar Meta");
    }
  }, []);

  /* ---- Sync ---- */
  const handleSync = useCallback(async () => {
    if (!selectedAccount) return;
    setSyncing(true);
    setSyncResult(null);
    try {
      const data = await apiFetch<SyncResult>("/campaigns/sync", {
        method: "POST",
        body: JSON.stringify({
          act_id: selectedAccount,
          date_preset: selectedPeriod,
        }),
      });
      setSyncResult(data);
      track("campaign_sync", {
        act_id: selectedAccount,
        date_preset: selectedPeriod,
        campaigns_synced: data.campaigns_synced,
      });
      await loadCampaigns();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Erro ao sincronizar");
    } finally {
      setSyncing(false);
    }
  }, [selectedAccount, selectedPeriod, loadCampaigns]);

  /* ---- Evaluate ---- */
  const handleEvaluate = useCallback(async () => {
    if (!selectedAccount) return;
    setEvaluating(true);
    setAlerts([]);
    try {
      const data = await apiFetch<{ alerts: RuleAlert[]; total: number }>(
        "/analysis/evaluate",
        {
          method: "POST",
          body: JSON.stringify({
            act_id: selectedAccount,
            date_preset: selectedPeriod,
          }),
        }
      );
      setAlerts(data.alerts);
      track("analysis_run", {
        kind: "evaluate",
        act_id: selectedAccount,
        date_preset: selectedPeriod,
        alerts_total: data.total,
      });
    } catch (err) {
      alert(err instanceof Error ? err.message : "Erro na avaliação");
    } finally {
      setEvaluating(false);
    }
  }, [selectedAccount, selectedPeriod]);

  /* ---- Analysis history ---- */
  const loadAnalysisHistory = useCallback(async () => {
    if (!selectedAccount) return;
    setLoadingHistory(true);
    try {
      const data = await apiFetch<AnalysisHistoryEntry[]>(
        `/analysis/history?act_id=${selectedAccount}`
      );
      if (mountedRef.current) setAnalysisHistory(data);
    } catch {
      /* silent */
    } finally {
      if (mountedRef.current) setLoadingHistory(false);
    }
  }, [selectedAccount]);

  useEffect(() => {
    if (section === "analysis" && selectedAccount) loadAnalysisHistory();
  }, [section, selectedAccount, loadAnalysisHistory]);

  /* ---- AI Summary ---- */
  const handleSummary = useCallback(async () => {
    if (!selectedAccount) return;
    setSummarizing(true);
    setAiSummary(null);
    try {
      const data = await apiFetch<AISummary>("/analysis/summary", {
        method: "POST",
        body: JSON.stringify({
          act_id: selectedAccount,
          date_preset: selectedPeriod,
          nivel_tecnico: "intermediario",
        }),
      });
      setAiSummary(data);
      track("analysis_run", {
        kind: "summary",
        act_id: selectedAccount,
        date_preset: selectedPeriod,
      });
      loadAnalysisHistory();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Erro no resumo IA");
    } finally {
      setSummarizing(false);
    }
  }, [selectedAccount, selectedPeriod, loadAnalysisHistory]);

  /* ---- Notifications ---- */
  const loadNotifications = useCallback(async () => {
    try {
      const data = await apiFetch<NotificationEntry[]>("/notifications?limit=50");
      if (mountedRef.current) setNotifications(data);
    } catch {
      /* silent */
    }
  }, []);

  useEffect(() => {
    loadNotifications();
    const interval = setInterval(loadNotifications, 60000);
    return () => clearInterval(interval);
  }, [loadNotifications]);

  const markNotificationRead = useCallback(async (id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, lida: true } : n))
    );
    try {
      await apiFetch(`/notifications/${id}/read`, { method: "POST" });
    } catch {
      /* silent */
    }
  }, []);

  const markAllNotificationsRead = useCallback(async () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, lida: true })));
    try {
      await apiFetch("/notifications/read-all", { method: "POST" });
    } catch {
      /* silent */
    }
  }, []);

  /* ---- Automation settings ---- */
  const loadAutomationSettings = useCallback(async () => {
    if (!selectedAccount) return;
    setLoadingAutomationSettings(true);
    try {
      const data = await apiFetch<AutomationSettings>(
        `/automation/settings?act_id=${selectedAccount}`
      );
      if (mountedRef.current) setAutomationSettings(data);
    } catch {
      /* silent */
    } finally {
      if (mountedRef.current) setLoadingAutomationSettings(false);
    }
  }, [selectedAccount]);

  useEffect(() => {
    if (section === "automation" && selectedAccount) loadAutomationSettings();
  }, [section, selectedAccount, loadAutomationSettings]);

  const updateAutomationSettings = useCallback(
    async (patch: Partial<AutomationSettings>) => {
      if (!selectedAccount) return;
      const next: AutomationSettings = {
        auto_pause_enabled: automationSettings?.auto_pause_enabled ?? false,
        server_schedule_enabled: automationSettings?.server_schedule_enabled ?? false,
        notify_email: automationSettings?.notify_email ?? true,
        notify_whatsapp: false,
        ...patch,
      };
      setAutomationSettings(next);
      try {
        const data = await apiFetch<AutomationSettings>("/automation/settings", {
          method: "PUT",
          body: JSON.stringify({
            act_id: selectedAccount,
            auto_pause_enabled: next.auto_pause_enabled,
            server_schedule_enabled: next.server_schedule_enabled,
            notify_email: next.notify_email,
          }),
        });
        if (mountedRef.current) setAutomationSettings(data);
        track("automation_toggle", { act_id: selectedAccount, patch });
      } catch (err) {
        alert(err instanceof Error ? err.message : "Erro ao salvar configuração");
        loadAutomationSettings();
      }
    },
    [selectedAccount, automationSettings, loadAutomationSettings]
  );

  const runAutomationNow = useCallback(async () => {
    if (!selectedAccount) return;
    setAutomationRunning(true);
    try {
      const data = await apiFetch<AutomationRunResult>("/automation/run", {
        method: "POST",
        body: JSON.stringify({ act_id: selectedAccount, date_preset: selectedPeriod }),
      });
      setLastAutomationRun(data);
      track("automation_manual_run", {
        act_id: selectedAccount,
        alerts_found: data.alerts_found,
        paused_count: data.paused_count,
      });
      await loadCampaigns();
      loadNotifications();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Erro ao rodar verificação");
    } finally {
      setAutomationRunning(false);
    }
  }, [selectedAccount, selectedPeriod, loadCampaigns, loadNotifications]);

  /* ---- Audit log ---- */
  const loadAuditLog = useCallback(async () => {
    setLoadingAudit(true);
    try {
      const data = await apiFetch<AuditEntry[]>("/audit-log?limit=50");
      if (mountedRef.current) setAuditLog(data);
    } catch {
      /* silent */
    } finally {
      if (mountedRef.current) setLoadingAudit(false);
    }
  }, []);

  useEffect(() => {
    if (section === "audit") loadAuditLog();
  }, [section, loadAuditLog]);

  /* ---- Campaign actions ---- */
  const handleCampaignAction = useCallback(
    async (campaignId: string, action: "activate" | "pause") => {
      setActionLoading(campaignId);
      try {
        await apiFetch(`/campaigns/${campaignId}/${action}`, { method: "POST" });
        await loadCampaigns();
      } catch (err) {
        alert(err instanceof Error ? err.message : "Erro na ação");
      } finally {
        setActionLoading(null);
      }
    },
    [loadCampaigns]
  );

  /* ---- Logout resets all state ---- */
  const handleLogout = useCallback(() => {
    setAccounts([]);
    setCampaigns([]);
    setAlerts([]);
    setAiSummary(null);
    setAuditLog([]);
    setAnalysisHistory([]);
    setAutomationSettings(null);
    setLastAutomationRun(null);
    setNotifications([]);
    setSelectedAccount("");
    setMetaConnected(false);
    try {
      localStorage.removeItem(LS_KEY);
    } catch {
      /* silent */
    }
    onLogout();
  }, [onLogout]);

  /* ---- derived ---- */
  const currentAccountName = useMemo(() => {
    const acc = accounts.find((a) => a.external_id === selectedAccount);
    return acc?.name || selectedAccount;
  }, [accounts, selectedAccount]);

  return (
    <div className={`app-shell${sidebarOpen ? "" : " sidebar-collapsed"}`}>
      <Sidebar
        section={section}
        setSection={setSection}
        sidebarOpen={sidebarOpen}
        setSidebarOpen={setSidebarOpen}
        userEmail={userEmail}
        onLogout={handleLogout}
      />

      <main className="workspace">
        <div className="account-selector">
          <div className="account-selector-inner">
            <div className="account-selector-controls">
              <AccountSelector
                accounts={accounts}
                selectedAccount={selectedAccount}
                onSelect={selectAccount}
              />
              <PeriodSelector value={selectedPeriod} onSelect={selectPeriod} />
            </div>
            <NotificationBell
              notifications={notifications}
              onMarkRead={markNotificationRead}
              onMarkAllRead={markAllNotificationsRead}
            />
          </div>
        </div>

        {section === "dashboard" && (
          <Dashboard
            accounts={accounts}
            selectedAccount={selectedAccount}
            setSelectedAccount={selectAccount}
            campaigns={campaigns}
            metaConnected={metaConnected}
            loadingAccounts={loadingAccounts}
            syncing={syncing}
            syncResult={syncResult}
            onRefresh={loadAccounts}
            onMetaConnect={handleMetaConnect}
            onSync={handleSync}
            onGoToAnalysis={() => setSection("analysis")}
          />
        )}

        {section === "campaigns" && (
          <CampaignsView
            selectedAccount={selectedAccount}
            campaigns={campaigns}
            loadingCampaigns={loadingCampaigns}
            syncing={syncing}
            syncResult={syncResult}
            actionLoading={actionLoading}
            onSync={handleSync}
            onCampaignAction={handleCampaignAction}
            onGoToDashboard={() => setSection("dashboard")}
          />
        )}

        {section === "analysis" && (
          <AnalysisView
            selectedAccount={selectedAccount}
            currentAccountName={currentAccountName}
            alerts={alerts}
            aiSummary={aiSummary}
            evaluating={evaluating}
            summarizing={summarizing}
            analysisHistory={analysisHistory}
            loadingHistory={loadingHistory}
            onEvaluate={handleEvaluate}
            onSummary={handleSummary}
            onGoToDashboard={() => setSection("dashboard")}
          />
        )}

        {section === "automation" && (
          <AutomationPanel
            selectedAccount={selectedAccount}
            currentAccountName={currentAccountName}
            settings={automationSettings}
            loadingSettings={loadingAutomationSettings}
            running={automationRunning}
            lastRunResult={lastAutomationRun}
            onUpdateSettings={updateAutomationSettings}
            onRunNow={runAutomationNow}
            onGoToDashboard={() => setSection("dashboard")}
          />
        )}

        {section === "audit" && (
          <AuditView
            auditLog={auditLog}
            loadingAudit={loadingAudit}
            onRefresh={loadAuditLog}
          />
        )}
      </main>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        .spin { animation: spin 1s linear infinite; }
      `}</style>
    </div>
  );
}
