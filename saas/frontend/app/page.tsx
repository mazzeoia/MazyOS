"use client";

import { useAuth } from "@/hooks/useAuth";
import AuthScreen from "@/components/AuthScreen";
import AppShell from "@/components/AppShell";

export default function GestorAds() {
  const auth = useAuth();

  if (!auth.authChecked) return null;

  if (!auth.authed) {
    return (
      <AuthScreen
        authMode={auth.authMode}
        authEmail={auth.authEmail}
        setAuthEmail={auth.setAuthEmail}
        authPass={auth.authPass}
        setAuthPass={auth.setAuthPass}
        authNome={auth.authNome}
        setAuthNome={auth.setAuthNome}
        authLoading={auth.authLoading}
        authError={auth.authError}
        handleAuth={auth.handleAuth}
        toggleMode={auth.toggleMode}
      />
    );
  }

  return <AppShell userEmail={auth.userEmail} onLogout={auth.handleLogout} />;
}
