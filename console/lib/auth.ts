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

export async function loginWithCognito(email: string, password: string): Promise<Session> {
  const clientId = process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID;
  const region = process.env.NEXT_PUBLIC_AWS_REGION || 'us-east-1';

  if (!clientId) {
    // If no client ID configured in env, fallback to simulated dev session
    const devSession: Session = {
      email,
      accessToken: `dev-token-${Date.now()}`,
      idToken: `dev-id-${Date.now()}`,
      expiresAt: Date.now() + 3600 * 1000,
    };
    saveSession(devSession);
    return devSession;
  }

  const endpoint = `https://cognito-idp.${region}.amazonaws.com/`;
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-amz-json-1.1',
      'X-Amz-Target': 'AWSCognitoIdentityProviderService.InitiateAuth',
    },
    body: JSON.stringify({
      AuthFlow: 'USER_PASSWORD_AUTH',
      ClientId: clientId,
      AuthParameters: {
        USERNAME: email,
        PASSWORD: password,
      },
    }),
  });

  const data = await response.json();

  if (!response.ok) {
    const errorMsg = data.__type ? `${data.__type.split('#').pop()}: ${data.message}` : data.message || 'Login failed';
    throw new Error(errorMsg);
  }

  const authResult = data.AuthenticationResult;
  if (!authResult || !authResult.AccessToken) {
    throw new Error('Authentication succeeded but no access token returned.');
  }

  const session: Session = {
    email,
    accessToken: authResult.AccessToken,
    idToken: authResult.IdToken || '',
    expiresAt: Date.now() + (authResult.ExpiresIn || 3600) * 1000,
  };

  saveSession(session);
  return session;
}

export function getAuthorizationHeader(): Record<string, string> {
  const session = getStoredSession();
  if (session?.accessToken) {
    return { Authorization: `Bearer ${session.accessToken}` };
  }
  return {};
}
