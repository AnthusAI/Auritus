'use client';

import React, { useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { getStoredSession } from '../lib/auth';

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [authorized, setAuthorized] = useState<boolean | null>(null);

  useEffect(() => {
    if (pathname === '/login' || pathname === '/callback') {
      setAuthorized(true);
      return;
    }

    const session = getStoredSession();
    if (!session?.accessToken) {
      setAuthorized(false);
      router.replace('/login');
    } else {
      setAuthorized(true);
    }
  }, [pathname, router]);

  if (authorized === null) {
    return (
      <div className="console-container" style={{ padding: '4rem 0', textAlign: 'center', color: 'var(--ink-muted)' }}>
        Checking authentication...
      </div>
    );
  }

  if (!authorized && pathname !== '/login') {
    return null;
  }

  return <>{children}</>;
}
