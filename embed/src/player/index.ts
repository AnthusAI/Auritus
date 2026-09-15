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

/**
 * Format a duration in seconds to a human-readable mm:ss string (or h:mm:ss).
 */
export function formatDuration(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) {
    return "0:00";
  }
  const totalSeconds = Math.floor(seconds);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const remainingSeconds = totalSeconds % 60;
  const paddedSeconds = remainingSeconds.toString().padStart(2, "0");
  if (hours > 0) {
    const paddedMinutes = minutes.toString().padStart(2, "0");
    return `${hours}:${paddedMinutes}:${paddedSeconds}`;
  }
  return `${minutes}:${paddedSeconds}`;
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
    <div class="auritus-pending">
      <button type="button" class="auritus-play" aria-label="Play">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" aria-hidden="true">
          <path d="M8 5.14v13.72a1 1 0 0 0 1.5.86l11-6.86a1 1 0 0 0 0-1.72l-11-6.86a1 1 0 0 0-1.5.86z"/>
        </svg>
      </button>
      <span class="auritus-status"></span>
    </div>
    <audio class="auritus-audio" controls hidden></audio>
    <p class="auritus-error" hidden></p>
  `;
  shadow.appendChild(root);

  const nameEl = root.querySelector(".auritus-name") as HTMLParagraphElement;
  const bylineEl = root.querySelector(".auritus-byline") as HTMLParagraphElement;
  const pendingEl = root.querySelector(".auritus-pending") as HTMLDivElement;
  const playBtn = root.querySelector(".auritus-play") as HTMLButtonElement;
  const statusEl = root.querySelector(".auritus-status") as HTMLSpanElement;
  const errorEl = root.querySelector(".auritus-error") as HTMLParagraphElement;
  // The real player: native browser media controls (scrubbing, volume,
  // and on Chromium/Edge a playback-speed menu) rather than a hand-built
  // play button and progress bar. Hidden until a job is done and has a
  // src -- an <audio controls> with nothing to play is confusing chrome,
  // not a player.
  const audio = root.querySelector(".auritus-audio") as HTMLAudioElement;
  // "metadata" (not "none"): fetches just the file header via a small
  // range request as soon as src is set, so the real duration is known
  // immediately once revealed, before the reader presses Play. The job
  // API's own duration_seconds field is claim-to-completion *processing*
  // time (used for perf stats elsewhere), not clip length -- there's no
  // shortcut around asking the browser to read the actual file.
  audio.preload = "metadata";

  nameEl.textContent = name;
  bylineEl.textContent = byline;
  if (!byline) {
    bylineEl.hidden = true;
  }

  let pollTimer: ReturnType<typeof setInterval> | undefined;
  let pendingPlay =
    host.parentElement?.getAttribute("data-auritus-play-intent") === "true";

  playBtn.disabled = false;
  if (pendingPlay) {
    statusEl.hidden = false;
    statusEl.textContent = "Starting when ready…";
  }

  function setError(message: string): void {
    errorEl.hidden = false;
    errorEl.textContent = message;
    // Nothing left to offer: no file exists to play, and none is coming.
    pendingEl.hidden = true;
  }

  function applyJob(job: JobRecord): void {
    if (job.status === "failed") {
      setError("Audio could not be generated.");
      stopPolling();
      return;
    }
    if (job.status === "done" && job.audio_url) {
      stopPolling();
      pendingEl.hidden = true;
      audio.hidden = false;
      audio.src = job.audio_url;
      // preload="metadata" fetches the file header on its own once src is
      // set, but some browsers need an explicit nudge to start that fetch
      // for an <audio> element that already existed before src changed.
      audio.load();
      if (pendingPlay) {
        pendingPlay = false;
        rewindIfEnded(audio);
        void audio.play();
      }
      return;
    }
    statusEl.hidden = false;
    statusEl.textContent = pendingPlay
      ? "Starting when ready…"
      : statusLabel(job);
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
        statusEl.textContent = pendingPlay
          ? "Starting when ready…"
          : "Waiting for audio…";
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

  // The pending-play button only ever requests an early start -- once a
  // job is done, applyJob() hides this button entirely and reveals native
  // <audio controls>, which has its own real play/pause button built in.
  playBtn.addEventListener("click", () => {
    pendingPlay = true;
    playBtn.disabled = true;
    statusEl.hidden = false;
    statusEl.textContent = "Starting when ready…";
  });

  // Native controls leave a finished clip sitting at its own end; reset it
  // so the reader's next click on the native play button starts over
  // instead of doing nothing.
  audio.addEventListener("ended", () => {
    rewindIfEnded(audio);
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
