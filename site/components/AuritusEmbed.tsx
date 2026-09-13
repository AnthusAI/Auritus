"use client";

import { useEffect, useRef } from "react";
import Script from "next/script";

type AuritusBoot = (options: { element: HTMLElement }) => Promise<HTMLElement>;

type AuritusGlobal = {
  boot?: AuritusBoot;
  disposePlayers?: () => void;
  default?: { boot?: AuritusBoot; disposePlayers?: () => void };
};

type AuritusEmbedProps = {
  siteKey: string;
  apiUrl?: string;
  name?: string;
  byline?: string;
  origin?: string;
  ttsBackend?: string;
  voiceId?: string;
  root?: string;
  playerHost?: string;
};

function resolveBoot(): AuritusBoot | undefined {
  if (typeof window === "undefined") {
    return undefined;
  }
  const global = (window as Window & { Auritus?: AuritusGlobal }).Auritus;
  return global?.boot ?? global?.default?.boot;
}

function resolveDispose(): (() => void) | undefined {
  if (typeof window === "undefined") {
    return undefined;
  }
  const global = (window as Window & { Auritus?: AuritusGlobal }).Auritus;
  return global?.disposePlayers ?? global?.default?.disposePlayers;
}

function waitForBoot(timeoutMs = 15_000): Promise<AuritusBoot> {
  const existing = resolveBoot();
  if (existing) {
    return Promise.resolve(existing);
  }
  return new Promise((resolve, reject) => {
    const started = Date.now();
    const timer = window.setInterval(() => {
      const boot = resolveBoot();
      if (boot) {
        window.clearInterval(timer);
        resolve(boot);
        return;
      }
      if (Date.now() - started >= timeoutMs) {
        window.clearInterval(timer);
        reject(new Error("Auritus embed: boot is not available"));
      }
    }, 50);
  });
}

/** First-paint player slot so example pages show chrome before embed.js boots. */
export function AuritusPlayerHost() {
  return (
    <div className="auritus-player-host">
      <p className="auritus-player-placeholder">Loading player</p>
    </div>
  );
}

export function AuritusEmbed({
  siteKey,
  apiUrl,
  name,
  byline,
  origin,
  ttsBackend = "kokoro",
  voiceId,
  root,
  playerHost,
}: AuritusEmbedProps) {
  const configRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const element = configRef.current;
    if (!element) {
      return;
    }
    let cancelled = false;
    let mounted: HTMLElement | undefined;

    void waitForBoot()
      .then(async (boot) => {
        if (cancelled) {
          return;
        }
        mounted = await boot({ element });
        if (cancelled) {
          mounted.dispatchEvent(new Event("auritus-dispose"));
          mounted.remove();
        }
      })
      .catch((err) => {
        if (!cancelled) {
          console.error(err);
        }
      });

    return () => {
      cancelled = true;
      if (mounted) {
        mounted.dispatchEvent(new Event("auritus-dispose"));
        mounted.remove();
      }
      resolveDispose()?.();
    };
  }, [
    siteKey,
    apiUrl,
    name,
    byline,
    origin,
    ttsBackend,
    voiceId,
    root,
    playerHost,
  ]);

  return (
    <>
      <div
        ref={configRef}
        data-auritus-site-key={siteKey}
        data-auritus-api={apiUrl}
        data-auritus-name={name}
        data-auritus-byline={byline}
        data-auritus-origin={origin}
        data-auritus-tts-backend={ttsBackend}
        data-auritus-voice={voiceId}
        data-auritus-root={root}
        data-auritus-player-host={playerHost}
      />
      <Script src="/embed.js" strategy="afterInteractive" />
    </>
  );
}
