/** Operator authentication and token management for Auritus Web Console. */

export interface Session {
  email: string;
  accessToken: string;
  idToken: string;
  expiresAt: number;
}

const SESSION_STORAGE_KEY = 'auritus_console_session';

export function getStoredSession(): Session | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = localStorage.getItem(SESSION_STORAGE_KEY);
    if (!raw) return null;
    const session = JSON.parse(raw) as Session;
    if (Date.now() > session.expiresAt) {
      localStorage.removeItem(SESSION_STORAGE_KEY);
      return null;
    }
    return session;
  } catch {
    return null;
  }
}

export function saveSession(session: Session): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
}

export function clearSession(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(SESSION_STORAGE_KEY);
}

export function getAuthorizationHeader(): Record<string, string> {
  const session = getStoredSession();
  if (session?.accessToken) {
    return { Authorization: `Bearer ${session.accessToken}` };
  }
  return {};
}
