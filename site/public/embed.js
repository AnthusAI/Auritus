"use strict";
var Auritus = (() => {
  var __defProp = Object.defineProperty;
  var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
  var __getOwnPropNames = Object.getOwnPropertyNames;
  var __hasOwnProp = Object.prototype.hasOwnProperty;
  var __export = (target, all) => {
    for (var name in all)
      __defProp(target, name, { get: all[name], enumerable: true });
  };
  var __copyProps = (to, from, except, desc) => {
    if (from && typeof from === "object" || typeof from === "function") {
      for (let key of __getOwnPropNames(from))
        if (!__hasOwnProp.call(to, key) && key !== except)
          __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
    }
    return to;
  };
  var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

  // src/index.ts
  var src_exports = {};
  __export(src_exports, {
    AURITUS_BREAK_MARKER: () => AURITUS_BREAK_MARKER,
    AuritusApiClient: () => AuritusApiClient,
    boot: () => boot,
    computeContentHash: () => computeContentHash,
    default: () => src_default,
    disposePlayers: () => disposePlayers,
    generateTtsText: () => generateTtsText,
    mountPlayer: () => mountPlayer,
    normalizeText: () => normalizeText,
    readEmbedConfig: () => readEmbedConfig,
    readEmbedMetadata: () => readEmbedMetadata,
    rewindIfEnded: () => rewindIfEnded
  });

  // src/api.ts
  var SITE_KEY_HEADER = "X-Auritus-Site-Key";
  var AuritusApiClient = class {
    baseUrl;
    siteKey;
    fetchImpl;
    constructor(options) {
      this.baseUrl = options.baseUrl.replace(/\/$/, "");
      this.siteKey = options.siteKey;
      this.fetchImpl = options.fetchImpl ?? fetch.bind(globalThis);
    }
    headers() {
      return {
        Accept: "application/json",
        "Content-Type": "application/json",
        [SITE_KEY_HEADER]: this.siteKey
      };
    }
    async createJob(body) {
      const response = await this.fetchImpl(`${this.baseUrl}/jobs`, {
        method: "POST",
        headers: this.headers(),
        body: JSON.stringify(body)
      });
      if (!response.ok) {
        throw new Error(
          `Auritus POST /jobs failed: ${response.status} ${await response.text()}`
        );
      }
      return await response.json();
    }
    async getJob(contentHash) {
      const response = await this.fetchImpl(
        `${this.baseUrl}/jobs/${encodeURIComponent(contentHash)}`,
        {
          method: "GET",
          headers: this.headers()
        }
      );
      if (!response.ok) {
        throw new Error(
          `Auritus GET /jobs/${contentHash} failed: ${response.status} ${await response.text()}`
        );
      }
      return await response.json();
    }
  };

  // src/generator/hash.ts
  var AURITUS_BREAK_MARKER = "[[auritus:break]]";
  function normalizeText(text) {
    return text.normalize("NFC").replace(/\s+/g, " ").trim();
  }
  var FNV_OFFSET_BASIS = 2166136261;
  var FNV_PRIME = 16777619;
  function fnv1a32(input) {
    let hash = FNV_OFFSET_BASIS;
    for (let i = 0; i < input.length; i++) {
      hash ^= input.charCodeAt(i);
      hash = Math.imul(hash, FNV_PRIME);
    }
    return (hash >>> 0).toString(16).padStart(8, "0");
  }
  function computeContentHash(text, voiceId, ttsBackend) {
    const payload = `${normalizeText(text)}\0${voiceId}\0${ttsBackend}`;
    return fnv1a32(payload);
  }

  // src/generator/metadata.ts
  function readEmbedMetadata(element) {
    const name = element.getAttribute("data-auritus-name")?.trim() || document.title.trim() || "";
    const byline = element.getAttribute("data-auritus-byline")?.trim() || location.hostname || "";
    return { name, byline };
  }

  // src/generator/index.ts
  var BUILTIN_IGNORE_SELECTOR = "[data-auritus-ignore]";
  function resolveRoot(root) {
    if (root instanceof Element) {
      return root;
    }
    if (typeof root === "string" && root.length > 0) {
      const el = document.querySelector(root);
      if (!el) {
        throw new Error(`Auritus generator: root not found: ${root}`);
      }
      return el;
    }
    if (!document.body) {
      throw new Error("Auritus generator: document.body is not available");
    }
    return document.body;
  }
  function elementMatchesIgnore(el, selectors) {
    if (el.hasAttribute("data-auritus-ignore")) {
      return true;
    }
    for (const selector of selectors) {
      if (selector && el.matches(selector)) {
        return true;
      }
    }
    return false;
  }
  function walkNode(node, ignoreSelectors, parts) {
    if (node.nodeType === Node.ELEMENT_NODE) {
      const el = node;
      const tag = el.tagName.toLowerCase();
      if (tag === "script" || tag === "style" || tag === "noscript" || tag === "template") {
        return;
      }
      if (elementMatchesIgnore(el, ignoreSelectors)) {
        return;
      }
      const pronounce = el.getAttribute("data-auritus-pronounce");
      if (pronounce !== null) {
        parts.push(pronounce);
        return;
      }
      if (el.hasAttribute("data-auritus-break")) {
        parts.push(AURITUS_BREAK_MARKER);
      }
      for (const child of el.childNodes) {
        walkNode(child, ignoreSelectors, parts);
      }
      return;
    }
    if (node.nodeType === Node.TEXT_NODE) {
      const value = node.textContent ?? "";
      if (value.length > 0) {
        parts.push(value);
      }
    }
  }
  function generateTtsText(config = {}) {
    const root = resolveRoot(config.root);
    const ignoreSelectors = [
      BUILTIN_IGNORE_SELECTOR,
      ...config.ignoreSelectors ?? []
    ];
    const parts = [];
    walkNode(root, ignoreSelectors, parts);
    const raw = parts.join(" ");
    return { text: normalizeText(raw) };
  }

  // src/player/styles.ts
  var PLAYER_STYLES = `
:host {
  display: block;
  font-family: var(--auritus-font, inherit);
  color: var(--auritus-fg, #14201a);
  background: var(--auritus-bg, #ffffff);
  border: 1px solid var(--auritus-border, rgba(20, 32, 26, 0.14));
  border-radius: var(--auritus-radius, 10px);
  box-shadow: var(--auritus-shadow, 0 8px 24px rgba(20, 32, 26, 0.08));
  box-sizing: border-box;
}

*, *::before, *::after {
  box-sizing: border-box;
}

.auritus-player {
  padding: 12px 14px;
  border-radius: inherit;
}

.auritus-meta {
  margin-bottom: 10px;
}

.auritus-name {
  font-size: 1rem;
  font-weight: 600;
  line-height: 1.3;
  margin: 0;
}

.auritus-byline {
  font-size: 0.875rem;
  opacity: 0.85;
  margin: 4px 0 0;
}

.auritus-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.auritus-play {
  appearance: none;
  border: none;
  cursor: pointer;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--auritus-accent, #2d5f3f);
  color: var(--auritus-play-fg, #ffffff);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: transform 0.1s ease, opacity 0.15s ease;
}

.auritus-play:hover:not(:disabled) {
  opacity: 0.92;
  transform: scale(1.04);
}

.auritus-play:active:not(:disabled) {
  transform: scale(0.96);
}

.auritus-play:focus-visible {
  outline: 2px solid var(--auritus-accent, #2d5f3f);
  outline-offset: 2px;
}

.auritus-play:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.auritus-play .auritus-icon-play {
  margin-left: 2px;
}

.auritus-play .auritus-icon-pause {
  display: none;
}

.auritus-play[data-playing="true"] .auritus-icon-play {
  display: none;
}

.auritus-play[data-playing="true"] .auritus-icon-pause {
  display: block;
}

.auritus-time {
  font-size: 0.75rem;
  font-variant-numeric: tabular-nums;
  opacity: 0.8;
  white-space: nowrap;
  user-select: none;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  flex-shrink: 0;
}

.auritus-time[hidden] {
  display: none;
}

.auritus-status {
  font-size: 0.8125rem;
  opacity: 0.9;
}

.auritus-track {
  flex: 1;
  height: 4px;
  border-radius: 999px;
  background: var(--auritus-track, color-mix(in srgb, currentColor 25%, transparent));
  overflow: hidden;
}

.auritus-track-fill {
  height: 100%;
  width: 0%;
  background: var(--auritus-accent, currentColor);
  transition: width 0.1s linear;
}

.auritus-error {
  color: var(--auritus-accent, #c00);
  font-size: 0.8125rem;
  margin-top: 8px;
}
`.trim();

  // src/player/index.ts
  var DEFAULT_POLL_MS = 2e3;
  function rewindIfEnded(media) {
    const durationKnown = Number.isFinite(media.duration) && media.duration > 0;
    const atEnd = media.ended || durationKnown && media.currentTime >= media.duration;
    if (atEnd) {
      media.currentTime = 0;
    }
  }
  function formatDuration(seconds) {
    if (!Number.isFinite(seconds) || seconds < 0) {
      return "0:00";
    }
    const totalSeconds = Math.floor(seconds);
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor(totalSeconds % 3600 / 60);
    const remainingSeconds = totalSeconds % 60;
    const paddedSeconds = remainingSeconds.toString().padStart(2, "0");
    if (hours > 0) {
      const paddedMinutes = minutes.toString().padStart(2, "0");
      return `${hours}:${paddedMinutes}:${paddedSeconds}`;
    }
    return `${minutes}:${paddedSeconds}`;
  }
  function statusLabel(job) {
    switch (job.status) {
      case "done":
        return "Ready";
      case "failed":
        return "Generation failed";
      case "processing":
        return "Generating audio\u2026";
      default:
        return "Waiting for audio\u2026";
    }
  }
  function mountPlayer(options) {
    const {
      host,
      api,
      contentHash,
      name,
      byline,
      pollIntervalMs = DEFAULT_POLL_MS
    } = options;
    const shadow = host.shadowRoot ?? host.attachShadow({ mode: "open" });
    shadow.replaceChildren();
    const style = document.createElement("style");
    style.textContent = PLAYER_STYLES;
    shadow.appendChild(style);
    const root = document.createElement("div");
    root.className = "auritus-player";
    root.innerHTML = `
    <div class="auritus-meta">
      <p class="auritus-name"></p>
      <p class="auritus-byline"></p>
    </div>
    <div class="auritus-controls">
      <button type="button" class="auritus-play" aria-label="Play" data-playing="false">
        <svg class="auritus-icon-play" viewBox="0 0 24 24" width="16" height="16" fill="currentColor" aria-hidden="true">
          <path d="M8 5.14v13.72a1 1 0 0 0 1.5.86l11-6.86a1 1 0 0 0 0-1.72l-11-6.86a1 1 0 0 0-1.5.86z"/>
        </svg>
        <svg class="auritus-icon-pause" viewBox="0 0 24 24" width="16" height="16" fill="currentColor" aria-hidden="true">
          <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
        </svg>
      </button>
      <div class="auritus-track" aria-hidden="true">
        <div class="auritus-track-fill"></div>
      </div>
      <span class="auritus-time" aria-label="Audio duration" hidden>
        <span class="auritus-time-current">0:00</span>
        <span class="auritus-time-separator">/</span>
        <span class="auritus-time-duration">0:00</span>
      </span>
      <span class="auritus-status"></span>
    </div>
    <p class="auritus-error" hidden></p>
  `;
    shadow.appendChild(root);
    const nameEl = root.querySelector(".auritus-name");
    const bylineEl = root.querySelector(".auritus-byline");
    const playBtn = root.querySelector(".auritus-play");
    const statusEl = root.querySelector(".auritus-status");
    const trackFill = root.querySelector(".auritus-track-fill");
    const errorEl = root.querySelector(".auritus-error");
    const timeEl = root.querySelector(".auritus-time");
    const timeCurrentEl = root.querySelector(
      ".auritus-time-current"
    );
    const timeDurationEl = root.querySelector(
      ".auritus-time-duration"
    );
    nameEl.textContent = name;
    bylineEl.textContent = byline;
    if (!byline) {
      bylineEl.hidden = true;
    }
    const audio = document.createElement("audio");
    audio.preload = "metadata";
    shadow.appendChild(audio);
    let pollTimer;
    let pendingPlay = host.parentElement?.getAttribute("data-auritus-play-intent") === "true";
    playBtn.disabled = false;
    if (pendingPlay) {
      statusEl.hidden = false;
      statusEl.textContent = "Starting when ready\u2026";
    }
    function setError(message) {
      errorEl.hidden = false;
      errorEl.textContent = message;
      playBtn.disabled = true;
    }
    function updateTimeDisplay() {
      timeCurrentEl.textContent = formatDuration(audio.currentTime);
      if (Number.isFinite(audio.duration) && audio.duration > 0) {
        timeDurationEl.textContent = formatDuration(audio.duration);
      }
    }
    function applyJob(job) {
      statusEl.hidden = false;
      statusEl.textContent = pendingPlay ? "Starting when ready\u2026" : statusLabel(job);
      if (job.status === "failed") {
        setError("Audio could not be generated.");
        stopPolling();
        return;
      }
      if (job.status === "done" && job.audio_url) {
        stopPolling();
        audio.src = job.audio_url;
        audio.load();
        playBtn.disabled = false;
        statusEl.hidden = true;
        timeEl.hidden = false;
        updateTimeDisplay();
        if (pendingPlay) {
          pendingPlay = false;
          rewindIfEnded(audio);
          void audio.play();
        }
      }
    }
    function stopPolling() {
      if (pollTimer !== void 0) {
        clearInterval(pollTimer);
        pollTimer = void 0;
      }
    }
    async function refresh() {
      try {
        const job = await api.getJob(contentHash);
        applyJob(job);
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        if (/\b404\b/.test(message)) {
          statusEl.hidden = false;
          statusEl.textContent = pendingPlay ? "Starting when ready\u2026" : "Waiting for audio\u2026";
          return;
        }
        setError(message);
        stopPolling();
      }
    }
    function startPolling() {
      void refresh();
      pollTimer = setInterval(() => {
        void refresh();
      }, pollIntervalMs);
    }
    function syncPlayLabel() {
      const playing = !audio.paused && !audio.ended;
      playBtn.setAttribute("data-playing", playing ? "true" : "false");
      playBtn.setAttribute("aria-label", playing ? "Pause" : "Play");
    }
    playBtn.addEventListener("click", () => {
      if (!audio.paused) {
        audio.pause();
        return;
      }
      if (!audio.src) {
        pendingPlay = true;
        statusEl.hidden = false;
        statusEl.textContent = "Starting when ready\u2026";
        return;
      }
      rewindIfEnded(audio);
      void audio.play();
    });
    audio.addEventListener("play", syncPlayLabel);
    audio.addEventListener("pause", syncPlayLabel);
    audio.addEventListener("ended", () => {
      syncPlayLabel();
      if (Number.isFinite(audio.duration) && audio.duration > 0) {
        timeCurrentEl.textContent = formatDuration(audio.duration);
        trackFill.style.width = "100%";
      }
    });
    audio.addEventListener("loadedmetadata", () => {
      updateTimeDisplay();
      timeEl.hidden = false;
    });
    audio.addEventListener("durationchange", updateTimeDisplay);
    audio.addEventListener("timeupdate", () => {
      updateTimeDisplay();
      if (!audio.duration || !Number.isFinite(audio.duration)) {
        trackFill.style.width = "0%";
        return;
      }
      const pct = audio.currentTime / audio.duration * 100;
      trackFill.style.width = `${pct}%`;
    });
    startPolling();
    host.addEventListener(
      "auritus-dispose",
      () => {
        stopPolling();
        audio.pause();
        audio.removeAttribute("src");
      },
      { once: true }
    );
    return host;
  }

  // src/index.ts
  function apiBaseFromElement(element) {
    const explicit = element.getAttribute("data-auritus-api")?.trim();
    if (explicit) {
      return explicit.replace(/\/$/, "");
    }
    if (element instanceof HTMLScriptElement) {
      try {
        const src = element.src;
        if (src) {
          const url = new URL(src);
          return url.origin;
        }
      } catch {
      }
    }
    return location.origin;
  }
  function parseListAttribute(value) {
    if (!value?.trim()) {
      return [];
    }
    return value.split(",").map((part) => part.trim()).filter(Boolean);
  }
  function readEmbedConfig(element) {
    const siteKey = element.getAttribute("data-auritus-site-key")?.trim();
    if (!siteKey) {
      throw new Error("Auritus embed: data-auritus-site-key is required");
    }
    return {
      siteKey,
      apiBaseUrl: apiBaseFromElement(element),
      voiceId: element.getAttribute("data-auritus-voice")?.trim() || "af_heart",
      ttsBackend: element.getAttribute("data-auritus-tts-backend")?.trim() || "kokoro",
      root: element.getAttribute("data-auritus-root")?.trim() || void 0,
      ignoreSelectors: parseListAttribute(
        element.getAttribute("data-auritus-ignore-selectors")
      ),
      playerHost: element.getAttribute("data-auritus-player-host")?.trim()
    };
  }
  var bootGeneration = 0;
  function disposePlayers(root = document) {
    for (const host of root.querySelectorAll(".auritus-root")) {
      host.dispatchEvent(new Event("auritus-dispose"));
      host.remove();
    }
  }
  async function boot(options = {}) {
    const generation = ++bootGeneration;
    const element = options.element ?? options.script ?? document.querySelector("[data-auritus-site-key]");
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
      ignoreSelectors: config.ignoreSelectors
    });
    const contentHash = computeContentHash(
      text,
      config.voiceId,
      config.ttsBackend
    );
    const api = new AuritusApiClient({
      baseUrl: config.apiBaseUrl,
      siteKey: config.siteKey
    });
    const host = document.createElement("div");
    host.className = "auritus-root";
    host.setAttribute("data-auritus-hash", contentHash);
    if (config.playerHost) {
      const mountPoint = document.querySelector(config.playerHost);
      if (!mountPoint) {
        throw new Error(
          `Auritus embed: player host not found: ${config.playerHost}`
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
      byline
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
        voice_id: config.voiceId
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
  function shouldAutoBoot() {
    const current = document.currentScript;
    return current instanceof HTMLScriptElement && current.hasAttribute("data-auritus-site-key");
  }
  function autoBoot() {
    if (!shouldAutoBoot()) {
      return;
    }
    void boot({ script: document.currentScript }).catch(
      (err) => {
        console.error(err);
      }
    );
  }
  if (typeof document !== "undefined" && shouldAutoBoot()) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", autoBoot);
    } else {
      autoBoot();
    }
  }
  var auritusGlobal = { boot, disposePlayers };
  var src_default = auritusGlobal;
  return __toCommonJS(src_exports);
})();
//# sourceMappingURL=embed.js.map