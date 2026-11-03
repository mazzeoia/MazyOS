/* ======================================================================
   API layer — token management + fetch wrapper
   ====================================================================== */

import type { AuthData } from "./types";

export function getToken(): string | null {
  try {
    return localStorage.getItem("gestor_token");
  } catch {
    return null;
  }
}

export function saveAuth(data: AuthData) {
  try {
    localStorage.setItem("gestor_token", data.access_token);
    localStorage.setItem("gestor_email", data.email);
    localStorage.setItem("gestor_user_id", data.user_id);
  } catch {
    /* noop */
  }
}

export function clearAuth() {
  try {
    localStorage.removeItem("gestor_token");
    localStorage.removeItem("gestor_email");
    localStorage.removeItem("gestor_user_id");
  } catch {
    /* noop */
  }
}

export function getUserEmail(): string {
  try {
    return localStorage.getItem("gestor_email") || "";
  } catch {
    return "";
  }
}

export async function apiFetch<T = unknown>(
  path: string,
  opts: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(opts.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (opts.body && typeof opts.body === "string")
    headers["Content-Type"] = "application/json";

  const res = await fetch(`/api${path}`, { ...opts, headers });

  if (res.status === 401) {
    clearAuth();
    window.location.reload();
    throw new Error("Sessão expirada");
  }

  const json = await res.json().catch(() => ({}));

  if (!res.ok) {
    throw new Error(
      (json as { detail?: string }).detail || `Erro ${res.status}`
    );
  }
  return json as T;
}
