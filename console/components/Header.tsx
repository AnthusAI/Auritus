'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { getStoredSession, clearSession } from '../lib/auth';

export default function Header() {
  const pathname = usePathname();
  const router = useRouter();
  const [operatorEmail, setOperatorEmail] = useState<string | null>(null);

  useEffect(() => {
    const session = getStoredSession();
    if (session?.email) {
      setOperatorEmail(session.email);
    }
  }, [pathname]);

  const handleLogout = () => {
    clearSession();
    setOperatorEmail(null);
    router.push('/login');
  };

  const navItems = [
    { label: 'Overview', href: '/' },
    { label: 'Job Explorer', href: '/jobs' },
    { label: 'Worker & Queue Health', href: '/workers' },
  ];

  return (
    <header style={{ borderBottom: '1px solid var(--line)', background: 'var(--card)' }}>
      <div className="console-container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBlock: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
          <Link href="/" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontFamily: 'Georgia, serif', fontSize: '1.4rem', fontWeight: 700 }}>
              Auritus <span style={{ color: 'var(--accent)', fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Console</span>
            </span>
          </Link>
          <nav style={{ display: 'flex', gap: '1rem' }}>
            {navItems.map((item) => {
              const active = pathname === item.href || (item.href !== '/' && pathname?.startsWith(item.href));
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  style={{
                    padding: '0.4rem 0.8rem',
                    borderRadius: '4px',
                    fontWeight: 600,
                    background: active ? 'var(--panel)' : 'transparent',
                    color: active ? 'var(--ink)' : 'var(--ink-muted)',
                  }}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          {operatorEmail ? (
            <>
              <span className="mono" style={{ fontSize: '0.8rem', color: 'var(--ink-muted)' }}>
                {operatorEmail}
              </span>
              <button onClick={handleLogout} className="button" style={{ fontSize: '0.8rem', padding: '0.35rem 0.65rem' }}>
                Logout
              </button>
            </>
          ) : (
            <Link href="/login" className="button button-primary" style={{ fontSize: '0.8rem', padding: '0.35rem 0.65rem' }}>
              Sign In
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
