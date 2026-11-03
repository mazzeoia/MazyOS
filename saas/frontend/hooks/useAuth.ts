"use client";

import { useCallback, useState, useEffect } from "react";
import { apiFetch, clearAuth, getToken, getUserEmail, saveAuth } from "@/lib/api";
import { track } from "@/lib/track";
import type { AuthData } from "@/lib/types";

export function useAuth() {
  const [authed, setAuthed] = useState(false);
  const [authChecked, setAuthChecked] = useState(false);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [authEmail, setAuthEmail] = useState("");
  const [authPass, setAuthPass] = useState("");
  const [authNome, setAuthNome] = useState("");
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState("");

  useEffect(() => {
    const token = getToken();
    if (token) setAuthed(true);
    setAuthChecked(true);
  }, []);

  const userEmail = authed ? getUserEmail() : "";

  const handleAuth = useCallback(async () => {
    setAuthLoading(true);
    setAuthError("");
    try {
      const endpoint =
        authMode === "register" ? "/auth/register" : "/auth/login";
      const body: Record<string, string> = {
        email: authEmail,
        password: authPass,
      };
      if (authMode === "register") body.nome = authNome || authEmail.split("@")[0];

      const data = await apiFetch<AuthData>(endpoint, {
        method: "POST",
        body: JSON.stringify(body),
      });
      saveAuth(data);
      setAuthed(true);
      track("login", { mode: authMode });
    } catch (err) {
      setAuthError(err instanceof Error ? err.message : "Erro ao autenticar");
    } finally {
      setAuthLoading(false);
    }
  }, [authMode, authEmail, authPass, authNome]);

  const handleLogout = useCallback(() => {
    clearAuth();
    setAuthed(false);
  }, []);

  const toggleMode = useCallback(() => {
    setAuthMode((m) => (m === "login" ? "register" : "login"));
    setAuthError("");
  }, []);

  return {
    authed,
    authChecked,
    authMode,
    authEmail,
    setAuthEmail,
    authPass,
    setAuthPass,
    authNome,
    setAuthNome,
    authLoading,
    authError,
    userEmail,
    handleAuth,
    handleLogout,
    toggleMode,
  };
}
