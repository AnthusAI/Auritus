import { afterEach, describe, expect, it, vi } from "vitest";
import type { AuritusApiClient, JobRecord } from "../src/api.js";
import {
  formatDuration,
  mountPlayer,
  rewindIfEnded,
} from "../src/player/index.js";

describe("rewindIfEnded", () => {
  it("rewinds when the clip has ended", () => {
    const media = { currentTime: 23, duration: 23, ended: true };
    rewindIfEnded(media);
    expect(media.currentTime).toBe(0);
  });

  it("rewinds when currentTime is at duration", () => {
    const media = { currentTime: 48.08, duration: 48.08, ended: false };
    rewindIfEnded(media);
    expect(media.currentTime).toBe(0);
  });

  it("leaves mid-clip playback alone", () => {
    const media = { currentTime: 4, duration: 23, ended: false };
    rewindIfEnded(media);
    expect(media.currentTime).toBe(4);
  });
});

describe("mountPlayer pending Play", () => {
  afterEach(() => {
    document.body.replaceChildren();
    vi.restoreAllMocks();
  });

  it("starts playback when audio arrives after Play", async () => {
    let job: JobRecord = { content_hash: "h", status: "pending" };
    const api = {
      getJob: async () => job,
    } as unknown as AuritusApiClient;
    const played: string[] = [];
    vi.spyOn(HTMLMediaElement.prototype, "play").mockImplementation(function (
      this: HTMLMediaElement,
    ) {
      played.push(this.src);
      return Promise.resolve();
    });

    const host = document.createElement("div");
    document.body.appendChild(host);
    mountPlayer({
      host,
      api,
      contentHash: "h",
      name: "Gettysburg",
      byline: "Lincoln",
      pollIntervalMs: 15,
    });

    const play = host.shadowRoot?.querySelector(
      ".auritus-play",
    ) as HTMLButtonElement;
    play.click();
    job = {
      content_hash: "h",
      status: "done",
      audio_url: "https://example.test/speech.wav",
    };
    await vi.waitFor(() => {
      expect(played.length).toBeGreaterThan(0);
    });
    expect(played[0]).toContain("speech.wav");
  });
});

describe("formatDuration", () => {
  it("formats zero and standard seconds to mm:ss", () => {
    expect(formatDuration(0)).toBe("0:00");
    expect(formatDuration(9)).toBe("0:09");
    expect(formatDuration(23)).toBe("0:23");
    expect(formatDuration(75)).toBe("1:15");
    expect(formatDuration(143)).toBe("2:23");
  });

  it("formats clips exceeding one hour to h:mm:ss", () => {
    expect(formatDuration(3665)).toBe("1:01:05");
  });

  it("gracefully handles invalid and negative numbers", () => {
    expect(formatDuration(-10)).toBe("0:00");
    expect(formatDuration(Number.NaN)).toBe("0:00");
    expect(formatDuration(Number.POSITIVE_INFINITY)).toBe("0:00");
  });
});

describe("mountPlayer controls and duration", () => {
  afterEach(() => {
    document.body.replaceChildren();
    vi.restoreAllMocks();
  });

  it("toggles play/pause icon states and updates duration indicators", async () => {
    const job: JobRecord = {
      content_hash: "test-hash",
      status: "done",
      audio_url: "https://example.test/speech.wav",
    };
    const api = {
      getJob: async () => job,
    } as unknown as AuritusApiClient;

    const host = document.createElement("div");
    document.body.appendChild(host);
    mountPlayer({
      host,
      api,
      contentHash: "test-hash",
      name: "Test Title",
      byline: "Test Author",
      pollIntervalMs: 15,
    });

    const playBtn = host.shadowRoot?.querySelector(
      ".auritus-play",
    ) as HTMLButtonElement;
    const playIcon = playBtn.querySelector(".auritus-icon-play");
    const pauseIcon = playBtn.querySelector(".auritus-icon-pause");
    const timeEl = host.shadowRoot?.querySelector(
      ".auritus-time",
    ) as HTMLSpanElement;
    const timeCurrentEl = host.shadowRoot?.querySelector(
      ".auritus-time-current",
    ) as HTMLSpanElement;
    const timeDurationEl = host.shadowRoot?.querySelector(
      ".auritus-time-duration",
    ) as HTMLSpanElement;
    const audio = host.shadowRoot?.querySelector("audio") as HTMLAudioElement;

    expect(playIcon).not.toBeNull();
    expect(pauseIcon).not.toBeNull();
    expect(playBtn.getAttribute("data-playing")).toBe("false");
    expect(playBtn.getAttribute("aria-label")).toBe("Play");

    // Wait for audio src to be assigned from job
    await vi.waitFor(() => {
      expect(audio.src).toContain("speech.wav");
    });
    expect(timeEl.hidden).toBe(false);

    // Simulate duration loaded
    Object.defineProperty(audio, "duration", {
      value: 143,
      writable: true,
      configurable: true,
    });
    audio.dispatchEvent(new Event("loadedmetadata"));
    expect(timeDurationEl.textContent).toBe("2:23");
    expect(timeCurrentEl.textContent).toBe("0:00");

    // Simulate play
    Object.defineProperty(audio, "paused", {
      value: false,
      writable: true,
      configurable: true,
    });
    audio.dispatchEvent(new Event("play"));
    expect(playBtn.getAttribute("data-playing")).toBe("true");
    expect(playBtn.getAttribute("aria-label")).toBe("Pause");

    // Simulate timeupdate at 25 seconds
    Object.defineProperty(audio, "currentTime", {
      value: 25,
      writable: true,
      configurable: true,
    });
    audio.dispatchEvent(new Event("timeupdate"));
    expect(timeCurrentEl.textContent).toBe("0:25");
    expect(timeDurationEl.textContent).toBe("2:23");

    // Simulate pause
    Object.defineProperty(audio, "paused", {
      value: true,
      writable: true,
      configurable: true,
    });
    audio.dispatchEvent(new Event("pause"));
    expect(playBtn.getAttribute("data-playing")).toBe("false");
    expect(playBtn.getAttribute("aria-label")).toBe("Play");
  });
});
