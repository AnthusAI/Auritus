import type { AuritusApiClient, JobRecord } from "../api.js";
import { PLAYER_STYLES } from "./styles.js";

export interface MountPlayerOptions {
  host: HTMLElement;
  api: AuritusApiClient;
  contentHash: string;
  name: string;
  byline: string;
  pollIntervalMs?: number;
}

const DEFAULT_POLL_MS = 2000;

/**
 * Move playback to the start when the clip has already finished.
 */
export function rewindIfEnded(media: {
  currentTime: number;
  duration: number;
  ended: boolean;
}): void {
  const durationKnown = Number.isFinite(media.duration) && media.duration > 0;
  const atEnd =
    media.ended || (durationKnown && media.currentTime >= media.duration);
  if (atEnd) {
    media.currentTime = 0;
  }
}

function statusLabel(job: JobRecord): string {
  switch (job.status) {
    case "done":
      return "Ready";
    case "failed":
      return "Generation failed";
    case "processing":
      return "Generating audio…";
    default:
      return "Waiting for audio…";
  }
}

/**
 * Mount a shadow-DOM player that polls the job API until audio is ready.
 */
export function mountPlayer(options: MountPlayerOptions): HTMLElement {
  const {
    host,
    api,
    contentHash,
    name,
    byline,
    pollIntervalMs = DEFAULT_POLL_MS,
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
      <button type="button" class="auritus-play" disabled aria-label="Play">Play</button>
      <div class="auritus-track" aria-hidden="true">
        <div class="auritus-track-fill"></div>
      </div>
      <span class="auritus-status"></span>
    </div>
    <p class="auritus-error" hidden></p>
  `;
  shadow.appendChild(root);

  const nameEl = root.querySelector(".auritus-name") as HTMLParagraphElement;
  const bylineEl = root.querySelector(".auritus-byline") as HTMLParagraphElement;
  const playBtn = root.querySelector(".auritus-play") as HTMLButtonElement;
  const statusEl = root.querySelector(".auritus-status") as HTMLSpanElement;
  const trackFill = root.querySelector(".auritus-track-fill") as HTMLDivElement;
  const errorEl = root.querySelector(".auritus-error") as HTMLParagraphElement;

  nameEl.textContent = name;
  bylineEl.textContent = byline;
  if (!byline) {
    bylineEl.hidden = true;
  }

  const audio = document.createElement("audio");
  audio.preload = "none";
  shadow.appendChild(audio);

  let pollTimer: ReturnType<typeof setInterval> | undefined;

  function setError(message: string): void {
    errorEl.hidden = false;
    errorEl.textContent = message;
    playBtn.disabled = true;
  }

  function applyJob(job: JobRecord): void {
    statusEl.hidden = false;
    statusEl.textContent = statusLabel(job);
    if (job.status === "failed") {
      setError("Audio could not be generated.");
      stopPolling();
      return;
    }
    if (job.status === "done" && job.audio_url) {
      stopPolling();
      audio.src = job.audio_url;
      playBtn.disabled = false;
      statusEl.hidden = true;
    }
  }

  function stopPolling(): void {
    if (pollTimer !== undefined) {
      clearInterval(pollTimer);
      pollTimer = undefined;
    }
  }

  async function refresh(): Promise<void> {
    try {
      const job = await api.getJob(contentHash);
      applyJob(job);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      if (/\b404\b/.test(message)) {
        statusEl.hidden = false;
        statusEl.textContent = "Waiting for audio…";
        return;
      }
      setError(message);
      stopPolling();
    }
  }

  function startPolling(): void {
    void refresh();
    pollTimer = setInterval(() => {
      void refresh();
    }, pollIntervalMs);
  }

  function syncPlayLabel(): void {
    const playing = !audio.paused && !audio.ended;
    playBtn.textContent = playing ? "Pause" : "Play";
    playBtn.setAttribute("aria-label", playing ? "Pause" : "Play");
  }

  playBtn.addEventListener("click", () => {
    if (!audio.paused) {
      audio.pause();
      return;
    }
    rewindIfEnded(audio);
    void audio.play();
  });

  audio.addEventListener("play", syncPlayLabel);
  audio.addEventListener("pause", syncPlayLabel);
  audio.addEventListener("ended", syncPlayLabel);

  audio.addEventListener("timeupdate", () => {
    if (!audio.duration || !Number.isFinite(audio.duration)) {
      trackFill.style.width = "0%";
      return;
    }
    const pct = (audio.currentTime / audio.duration) * 100;
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
    { once: true },
  );

  return host;
}
