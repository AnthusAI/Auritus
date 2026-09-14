'use client';

import React, { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { exchangeSsoCode } from '../../lib/auth';

function CallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function processCode() {
      const code = searchParams ? searchParams.get('code') : null;
      const urlError = searchParams ? searchParams.get('error') : null;

      if (urlError) {
        setError(searchParams ? searchParams.get('error_description') || urlError : urlError);
        return;
      }

      if (!code) {
        setError('No authorization code received from identity provider.');
        return;
      }

      try {
        await exchangeSsoCode(code);
        router.push('/');
      } catch (err: any) {
        setError(err.message || 'Failed to complete SSO authentication.');
      }
    }

    processCode();
  }, [searchParams, router]);

  if (error) {
    return (
      <div className="console-container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <div className="card" style={{ maxWidth: '450px', padding: '2rem', textAlign: 'center' }}>
          <h2 style={{ color: 'var(--danger)', marginBottom: '1rem' }}>Authentication Failed</h2>
          <p style={{ color: 'var(--ink-muted)', marginBottom: '1.5rem', fontSize: '0.9rem' }}>{error}</p>
          <button onClick={() => router.push('/login')} className="button button-primary" style={{ width: '100%' }}>
            Return to Sign In
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="console-container" style={{ padding: '5rem 0', textAlign: 'center', color: 'var(--ink-muted)' }}>
      Completing single sign-on authentication...
    </div>
  );
}

export default function CallbackPage() {
  return (
    <Suspense fallback={<div className="console-container" style={{ padding: '5rem 0', textAlign: 'center' }}>Loading...</div>}>
      <CallbackContent />
    </Suspense>
  );
}
