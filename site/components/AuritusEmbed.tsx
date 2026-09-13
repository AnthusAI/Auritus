"use client";

import Script from "next/script";

type AuritusEmbedProps = {
  siteKey: string;
  apiUrl?: string;
  name?: string;
  byline?: string;
  origin?: string;
  ttsBackend?: string;
  root?: string;
};

export function AuritusEmbed({
  siteKey,
  apiUrl,
  name,
  byline,
  origin,
  ttsBackend = "kokoro",
  root,
}: AuritusEmbedProps) {
  return (
    <>
      <div
        data-auritus-site-key={siteKey}
        data-auritus-api={apiUrl}
        data-auritus-name={name}
        data-auritus-byline={byline}
        data-auritus-origin={origin}
        data-auritus-tts-backend={ttsBackend}
        data-auritus-root={root}
      />
      <Script
        src="/embed.js"
        strategy="afterInteractive"
        data-auritus-site-key={siteKey}
        data-auritus-api={apiUrl}
        data-auritus-name={name}
        data-auritus-byline={byline}
        data-auritus-origin={origin}
        data-auritus-tts-backend={ttsBackend}
        data-auritus-root={root}
      />
    </>
  );
}
