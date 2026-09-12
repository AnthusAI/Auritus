import { AuritusApiClient } from "./api.js";
import {
  computeContentHash,
  generateTtsText,
  readEmbedMetadata,
} from "./generator/index.js";
import { mountPlayer } from "./player/index.js";

export { AuritusApiClient } from "./api.js";
export type { CreateJobBody, JobRecord, JobStatus } from "./api.js";
export {
  computeContentHash,
  generateTtsText,
  normalizeText,
  readEmbedMetadata,
  AURITUS_BREAK_MARKER,
} from "./generator/index.js";
export { mountPlayer } from "./player/index.js";

export interface EmbedScriptConfig {
  siteKey: string;
  apiBaseUrl: string;
  voiceId: string;
  ttsBackend: string;
  root?: string;
  ignoreSelectors: string[];
  playerHost?: string;
}

function apiBaseFromScript(script: HTMLScriptElement): string {
  const explicit = script.getAttribute("data-auritus-api")?.trim();
  if (explicit) {
    return explicit.replace(/\/$/, "");
  }
  try {
    const src = script.src;
    if (src) {
      const url = new URL(src);
      return url.origin;
    }
  } catch {
    /* use location */
  }
  return location.origin;
}

function parseListAttribute(value: string | null): string[] {
  if (!value?.trim()) {
    return [];
  }
  return value
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean);
}

/**
 * Read configuration from the embed script element.
 */
export function readEmbedConfig(script: HTMLScriptElement): EmbedScriptConfig {
  const siteKey = script.getAttribute("data-auritus-site-key")?.trim();
  if (!siteKey) {
    throw new Error("Auritus embed: data-auritus-site-key is required");
  }
  return {
    siteKey,
    apiBaseUrl: apiBaseFromScript(script),
    voiceId: script.getAttribute("data-auritus-voice")?.trim() || "default",
    ttsBackend:
      script.getAttribute("data-auritus-tts-backend")?.trim() || "higgs",
    root: script.getAttribute("data-auritus-root")?.trim() || undefined,
    ignoreSelectors: parseListAttribute(
      script.getAttribute("data-auritus-ignore-selectors"),
    ),
    playerHost: script.getAttribute("data-auritus-player-host")?.trim(),
  };
}

export interface BootOptions {
  script?: HTMLScriptElement;
}

/**
 * Run generator, enqueue a job, and mount the player.
 */
export async function boot(options: BootOptions = {}): Promise<HTMLElement> {
  const script =
    options.script ??
    (document.querySelector(
      "script[data-auritus-site-key]",
    ) as HTMLScriptElement | null);
  if (!script) {
    throw new Error("Auritus embed: script[data-auritus-site-key] not found");
  }

  const config = readEmbedConfig(script);
  const { name, byline } = readEmbedMetadata(script);
  const { text } = generateTtsText({
    root: config.root,
    ignoreSelectors: config.ignoreSelectors,
  });
  const contentHash = computeContentHash(
    text,
    config.voiceId,
  );

  const api = new AuritusApiClient({
    baseUrl: config.apiBaseUrl,
    siteKey: config.siteKey,
  });

  await api.createJob({
    content_hash: contentHash,
    text,
    name,
    byline,
    tts_backend: config.ttsBackend ?? "kokoro",
    voice_id: config.voiceId,
  });

  const host = document.createElement("div");
  host.className = "auritus-root";
  host.setAttribute("data-auritus-hash", contentHash);

  if (config.playerHost) {
    const mountPoint = document.querySelector(config.playerHost);
    if (!mountPoint) {
      throw new Error(
        `Auritus embed: player host not found: ${config.playerHost}`,
      );
    }
    mountPoint.appendChild(host);
  } else {
    script.insertAdjacentElement("afterend", host);
  }

  return mountPlayer({
    host,
    api,
    contentHash,
    name,
    byline,
  });
}

function shouldAutoBoot(): boolean {
  const current = document.currentScript;
  return (
    current instanceof HTMLScriptElement &&
    current.hasAttribute("data-auritus-site-key")
  );
}

function autoBoot(): void {
  if (!shouldAutoBoot()) {
    return;
  }
  void boot({ script: document.currentScript as HTMLScriptElement }).catch(
    (err) => {
      console.error(err);
    },
  );
}

if (typeof document !== "undefined" && shouldAutoBoot()) {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", autoBoot);
  } else {
    autoBoot();
  }
}

const auritusGlobal = { boot };
export default auritusGlobal;
