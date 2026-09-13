'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { saveSession } from '../../lib/auth';

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
      // Authenticate against Cognito User Pool via API or simulated login
      // Session expires in 1 hour
      const mockSession = {
        email,
        accessToken: `jwt-${btoa(email)}-${Date.now()}`,
        idToken: `id-${btoa(email)}-${Date.now()}`,
        expiresAt: Date.now() + 3600 * 1000,
      };
      saveSession(mockSession);
      router.push('/');
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="console-container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '70vh' }}>
      <div className="card" style={{ width: '100%', maxWidth: '400px', padding: '2rem' }}>
        <h2 style={{ marginBottom: '0.5rem', textAlign: 'center' }}>Operator Sign In</h2>
        <p style={{ color: 'var(--ink-muted)', fontSize: '0.875rem', textAlign: 'center', marginBottom: '1.5rem' }}>
          Access Auritus job monitoring and infrastructure controls.
        </p>

        {error && (
          <div style={{ background: 'var(--danger-bg)', color: 'var(--danger)', padding: '0.75rem', borderRadius: '4px', marginBottom: '1rem', fontSize: '0.85rem' }}>
            {error}
          </div>
        )}

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
