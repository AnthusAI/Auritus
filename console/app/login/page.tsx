'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { loginWithCognito, getSsoAuthorizeUrl } from '../../lib/auth';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await loginWithCognito(email, password);
      router.push('/');
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSsoRedirect = (provider: 'Google' | 'IdentityCenter') => {
    const targetUrl = getSsoAuthorizeUrl(provider);
    window.location.href = targetUrl;
  };

  return (
    <div className="console-container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '70vh' }}>
      <div className="card" style={{ width: '100%', maxWidth: '420px', padding: '2rem' }}>
        <h2 style={{ marginBottom: '0.5rem', textAlign: 'center' }}>Operator Sign In</h2>
        <p style={{ color: 'var(--ink-muted)', fontSize: '0.875rem', textAlign: 'center', marginBottom: '1.5rem' }}>
          Access Auritus job monitoring and infrastructure controls.
        </p>

        {error && (
          <div style={{ background: 'var(--danger-bg)', color: 'var(--danger)', padding: '0.75rem', borderRadius: '4px', marginBottom: '1rem', fontSize: '0.85rem' }}>
            {error}
          </div>
        )}

        {/* Enterprise SSO Options */}
        <div style={{ display: 'grid', gap: '0.75rem', marginBottom: '1.5rem' }}>
          <button
            type="button"
            onClick={() => handleSsoRedirect('Google')}
            className="button"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.6rem',
              padding: '0.65rem',
              width: '100%',
              fontSize: '0.88rem',
              fontWeight: 600,
              background: '#fff',
              border: '1px solid var(--line)',
            }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
              />
            </svg>
            Sign In with Google Workspace
          </button>

          <button
            type="button"
            onClick={() => handleSsoRedirect('IdentityCenter')}
            className="button"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.6rem',
              padding: '0.65rem',
              width: '100%',
              fontSize: '0.88rem',
              fontWeight: 600,
              background: '#fff',
              border: '1px solid var(--line)',
            }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" />
            </svg>
            Sign In with AWS IAM Identity Center
          </button>
        </div>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            marginBlock: '1.25rem',
            gap: '1rem',
            color: 'var(--ink-muted)',
            fontSize: '0.75rem',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
          }}
        >
          <div style={{ flex: 1, height: '1px', background: 'var(--line)' }} />
          <span>Or with Cognito credentials</span>
          <div style={{ flex: 1, height: '1px', background: 'var(--line)' }} />
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'grid', gap: '1rem' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', marginBottom: '0.35rem' }}>
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              style={{ width: '100%', padding: '0.6rem', borderRadius: '4px', border: '1px solid var(--line)', background: '#fff', fontSize: '0.9rem' }}
              placeholder="operator@example.com"
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', marginBottom: '0.35rem' }}>
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={{ width: '100%', padding: '0.6rem', borderRadius: '4px', border: '1px solid var(--line)', background: '#fff', fontSize: '0.9rem' }}
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="button button-primary"
            style={{ width: '100%', padding: '0.75rem', marginTop: '0.5rem' }}
          >
            {loading ? 'Authenticating...' : 'Sign In with Cognito'}
          </button>
        </form>
      </div>
    </div>
  );
}
