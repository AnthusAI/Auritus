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
  AURITUS_PAUSE_MARKER,
  AURITUS_VOICE_RESET_MARKER,
  formatVoiceMarker,
} from "./generator/index.js";
export { mountPlayer, rewindIfEnded } from "./player/index.js";

/**
 * Configuration options parsed from an Auritus embed script or container tag.
 */
export interface EmbedScriptConfig {
  siteKey: string;
  apiBaseUrl: string;
  voiceId: string;
  ttsBackend: string;
  root?: string;
  ignoreSelectors: string[];
  playerHost?: string;
}

/**
 * Resolve the default voice ID for a given TTS backend.
 */
export function resolveDefaultVoice(ttsBackend: string): string {
  const backend = (ttsBackend || "kokoro").trim().toLowerCase();
  switch (backend) {
    case "kokoro":
      return "af_heart";
    case "qwen":
      return "Ryan";
    case "fish":
    case "chatterbox":
      return "narrator";
    default:
      return "default";
  }
}

function apiBaseFromElement(element: HTMLElement): string {
  const explicit = element.getAttribute("data-auritus-api")?.trim();
  if (explicit) {
    return explicit.replace(/\/$/, "");
  }
  let fallback = location.origin;
  if (element instanceof HTMLScriptElement) {
    try {
      const src = element.src;
      if (src) {
        const url = new URL(src);
        fallback = url.origin;
      }
    } catch {
      /* use location */
    }
  }
  console.warn(
    `Auritus embed: data-auritus-api is not set. Falling back to "${fallback}". ` +
      "If your embed is served from a CDN or static host, set " +
      'data-auritus-api="https://YOUR_API_GATEWAY_URL" on the script tag.',
  );
  return fallback;
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
 * Read configuration from the embed script or config element.
 */
export function readEmbedConfig(element: HTMLElement): EmbedScriptConfig {
  const siteKey = element.getAttribute("data-auritus-site-key")?.trim();
  if (!siteKey) {
    throw new Error("Auritus embed: data-auritus-site-key is required");
  }
  const ttsBackend =
    element.getAttribute("data-auritus-tts-backend")?.trim() || "kokoro";
  const explicitVoice = element.getAttribute("data-auritus-voice")?.trim();
  const voiceId = explicitVoice || resolveDefaultVoice(ttsBackend);

  return {
    siteKey,
    apiBaseUrl: apiBaseFromElement(element),
    voiceId,
    ttsBackend,
    root: element.getAttribute("data-auritus-root")?.trim() || undefined,
    ignoreSelectors: parseListAttribute(
      element.getAttribute("data-auritus-ignore-selectors"),
    ),
    playerHost: element.getAttribute("data-auritus-player-host")?.trim(),
  };
}

/**
 * Options for programmatically booting the Auritus embed script.
 */
export interface BootOptions {
  script?: HTMLScriptElement;
  element?: HTMLElement;
}

let bootGeneration = 0;

/**
 * Stop polling and remove every mounted Auritus player.
 */
export function disposePlayers(root: ParentNode = document): void {
  for (const host of root.querySelectorAll(".auritus-root")) {
    host.dispatchEvent(new Event("auritus-dispose"));
    host.remove();
  }
}

/**
 * Run generator, enqueue a job, and mount the player.
 */
export async function boot(options: BootOptions = {}): Promise<HTMLElement> {
  const generation = ++bootGeneration;
  const element =
    options.element ??
    options.script ??
    (document.querySelector("[data-auritus-site-key]") as HTMLElement | null);
  if (!element) {
    throw new Error("Auritus embed: [data-auritus-site-key] not found");
  }

  if (generation !== bootGeneration) {
    const skipped = document.createElement("div");
    skipped.setAttribute("data-auritus-boot-skipped", "true");
    return skipped;
  }

  disposePlayers();

  if (generation !== bootGeneration) {
    const skipped = document.createElement("div");
    skipped.setAttribute("data-auritus-boot-skipped", "true");
    return skipped;
  }

  const config = readEmbedConfig(element);
  const { name, byline } = readEmbedMetadata(element);
  const { text } = generateTtsText({
    root: config.root,
    ignoreSelectors: config.ignoreSelectors,
  });
  const contentHash = computeContentHash(
    text,
    config.voiceId,
    config.ttsBackend,
  );

  const api = new AuritusApiClient({
    baseUrl: config.apiBaseUrl,
    siteKey: config.siteKey,
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
    element.insertAdjacentElement("afterend", host);
  }

  const mounted = mountPlayer({
    host,
    api,
    contentHash,
    name,
    byline,
  });

  if (generation !== bootGeneration) {
    mounted.dispatchEvent(new Event("auritus-dispose"));
    mounted.remove();
    const skipped = document.createElement("div");
    skipped.setAttribute("data-auritus-boot-skipped", "true");
    return skipped;
  }

  try {
    await api.createJob({
      content_hash: contentHash,
      text,
      name,
      byline,
      tts_backend: config.ttsBackend ?? "kokoro",
      voice_id: config.voiceId,
    });
  } catch (err) {
    if (generation === bootGeneration) {
      const errorEl = host.shadowRoot?.querySelector(".auritus-error");
      if (errorEl instanceof HTMLElement) {
        errorEl.hidden = false;
        errorEl.textContent = err instanceof Error ? err.message : String(err);
      }
    }
    throw err;
  }

  if (generation !== bootGeneration) {
    mounted.dispatchEvent(new Event("auritus-dispose"));
    mounted.remove();
    const skipped = document.createElement("div");
    skipped.setAttribute("data-auritus-boot-skipped", "true");
    return skipped;
  }

  return mounted;
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

const auritusGlobal = { boot, disposePlayers };
export default auritusGlobal;
