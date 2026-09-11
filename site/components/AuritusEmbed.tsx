"use client";

import { useEffect } from "react";

type Props = {
  siteKey?: string;
  name?: string;
  byline?: string;
  apiEndpoint?: string;
  bg?: string;
  fg?: string;
  accent?: string;
  font?: string;
  ignore?: string;
};

/**
 * Loads the Auritus embed against the configured API for acceptance fixtures.
 */
export function AuritusEmbed(props: Props) {
  useEffect(() => {
    const api =
      props.apiEndpoint ||
      process.env.NEXT_PUBLIC_AURITUS_API_ENDPOINT ||
      "https://api.aurit.us";
    (window as Window & { AURITUS_API_ENDPOINT?: string }).AURITUS_API_ENDPOINT =
      api;

    const existing = document.querySelector("script[data-auritus-boot]");
    if (existing) {
      existing.remove();
    }
    const script = document.createElement("script");
    script.src = process.env.NEXT_PUBLIC_AURITUS_EMBED_SRC || "/embed.js";
    script.async = true;
    script.dataset.auritusBoot = "1";
    script.dataset.auritusSiteKey = props.siteKey || "demo-site-key";
    script.dataset.auritusApi = api;
    if (props.name) script.dataset.auritusName = props.name;
    if (props.byline) script.dataset.auritusByline = props.byline;
    if (props.bg) script.dataset.auritusBg = props.bg;
    if (props.fg) script.dataset.auritusFg = props.fg;
    if (props.accent) script.dataset.auritusAccent = props.accent;
    if (props.font) script.dataset.auritusFont = props.font;
    if (props.ignore) script.dataset.auritusIgnore = props.ignore;
    document.body.appendChild(script);
    return () => {
      script.remove();
    };
  }, [props]);

  return null;
}
