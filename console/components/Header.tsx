'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { Menu, X, LogOut } from 'lucide-react';
import { getStoredSession, clearSession } from '../lib/auth';

const navItems = [
  { label: 'Overview', href: '/' },
  { label: 'Job Explorer', href: '/jobs' },
  { label: 'Costs', href: '/costs' },
  { label: 'Sites', href: '/sites' },
  { label: 'Worker & Queue Health', href: '/workers' },
];

export default function Header() {
  const pathname = usePathname();
  const router = useRouter();
  const [operatorEmail, setOperatorEmail] = useState<string | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const session = getStoredSession();
    if (session?.email) {
      setOperatorEmail(session.email);
    }
  }, [pathname]);

  // Close the mobile menu on navigation.
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [pathname]);

  const handleLogout = () => {
    clearSession();
    setOperatorEmail(null);
    router.push('/login');
  };

  function isActive(href: string): boolean {
    return pathname === href || (href !== '/' && pathname?.startsWith(href));
  }

  return (
    <header style={{ borderBottom: '1px solid var(--line)', background: 'var(--card)' }}>
      <div className="console-container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBlock: '1rem' }}>
        <Link href="/" style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.15 }}>
          <span style={{ fontFamily: 'Georgia, serif', fontSize: '1.4rem', fontWeight: 700 }}>
            Auritus
          </span>
          <span style={{ color: 'var(--accent)', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
            Console
          </span>
        </Link>

        <div className="header-desktop-nav" style={{ alignItems: 'center', gap: '2rem' }}>
          <nav style={{ display: 'flex', gap: '1rem' }}>
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                style={{
                  padding: '0.4rem 0.8rem',
                  borderRadius: '4px',
                  fontWeight: 600,
                  background: isActive(item.href) ? 'var(--panel)' : 'transparent',
                  color: isActive(item.href) ? 'var(--ink)' : 'var(--ink-muted)',
                }}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>

        <div className="header-desktop-account" style={{ flexDirection: 'column', alignItems: 'flex-end', gap: '0.3rem' }}>
          {operatorEmail ? (
            <>
              <span className="mono" style={{ fontSize: '0.8rem', color: 'var(--ink-muted)' }}>
                {operatorEmail}
              </span>
              <button onClick={handleLogout} className="button" style={{ fontSize: '0.8rem', padding: '0.35rem 0.65rem' }}>
                <LogOut size={14} style={{ marginRight: '0.35rem', verticalAlign: '-2px' }} />
                Logout
              </button>
            </>
          ) : (
            <Link href="/login" className="button button-primary" style={{ fontSize: '0.8rem', padding: '0.35rem 0.65rem' }}>
              Sign In
            </Link>
          )}
        </div>

        <button
          className="header-mobile-toggle"
          onClick={() => setMobileMenuOpen((v) => !v)}
          aria-label={mobileMenuOpen ? 'Close menu' : 'Open menu'}
          aria-expanded={mobileMenuOpen}
          style={{
            alignItems: 'center',
            justifyContent: 'center',
            background: 'transparent',
            border: '1px solid var(--line)',
            borderRadius: '6px',
            padding: '0.4rem',
            cursor: 'pointer',
            color: 'var(--ink)',
          }}
        >
          {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      <div className={`header-mobile-panel${mobileMenuOpen ? ' open' : ''}`} style={{ flexDirection: 'column', borderTop: '1px solid var(--line)' }}>
        <nav className="console-container" style={{ display: 'flex', flexDirection: 'column', paddingBlock: '0.75rem', gap: '0.25rem' }}>
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              style={{
                padding: '0.6rem 0.8rem',
                borderRadius: '4px',
                fontWeight: 600,
                background: isActive(item.href) ? 'var(--panel)' : 'transparent',
                color: isActive(item.href) ? 'var(--ink)' : 'var(--ink-muted)',
              }}
            >
              {item.label}
            </Link>
          ))}
          <div style={{ borderTop: '1px solid var(--line)', marginTop: '0.5rem', paddingTop: '0.75rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.75rem' }}>
            {operatorEmail ? (
              <>
                <span className="mono" style={{ fontSize: '0.8rem', color: 'var(--ink-muted)' }}>
                  {operatorEmail}
                </span>
                <button onClick={handleLogout} className="button" style={{ fontSize: '0.8rem', padding: '0.35rem 0.65rem' }}>
                  <LogOut size={14} style={{ marginRight: '0.35rem', verticalAlign: '-2px' }} />
                  Logout
                </button>
              </>
            ) : (
              <Link href="/login" className="button button-primary" style={{ fontSize: '0.8rem', padding: '0.35rem 0.65rem' }}>
                Sign In
              </Link>
            )}
          </div>
        </nav>
      </div>
    </header>
  );
}
