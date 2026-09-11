"use client";

import Script from "next/script";

type AuritusEmbedProps = {
  siteKey: string;
  name?: string;
  byline?: string;
  origin?: string;
};

export function AuritusEmbed({
  siteKey,
  name,
  byline,
  origin,
}: AuritusEmbedProps) {
  return (
    <>
      <div
        data-auritus-site-key={siteKey}
        data-auritus-name={name}
        data-auritus-byline={byline}
        data-auritus-origin={origin}
      />
      <Script
        src="/embed.js"
        strategy="afterInteractive"
        data-auritus-site-key={siteKey}
        data-auritus-name={name}
        data-auritus-byline={byline}
        data-auritus-origin={origin}
      />
    </>
  );
}
