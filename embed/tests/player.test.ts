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

  it("starts playback when audio arrives after Play, and reveals native controls", async () => {
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

    const pendingEl = host.shadowRoot?.querySelector(
      ".auritus-pending",
    ) as HTMLDivElement;
    const play = host.shadowRoot?.querySelector(
      ".auritus-play",
    ) as HTMLButtonElement;
    const audio = host.shadowRoot?.querySelector("audio") as HTMLAudioElement;

    expect(pendingEl.hidden).toBe(false);
    expect(audio.hidden).toBe(true);

    play.click();
    expect(play.disabled).toBe(true);

    job = {
      content_hash: "h",
      status: "done",
      audio_url: "https://example.test/speech.wav",
    };
    await vi.waitFor(() => {
      expect(played.length).toBeGreaterThan(0);
    });
    expect(played[0]).toContain("speech.wav");
    // The button-and-status UI is gone; the real player -- native controls
    // with a src -- is what's left.
    expect(pendingEl.hidden).toBe(true);
    expect(audio.hidden).toBe(false);
    expect(audio.hasAttribute("controls")).toBe(true);
    expect(audio.src).toContain("speech.wav");
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

describe("mountPlayer duration fetch", () => {
  afterEach(() => {
    document.body.replaceChildren();
    vi.restoreAllMocks();
  });

  it("requests metadata as soon as the job is done, not only on play", async () => {
    // The job API's own duration_seconds is claim-to-completion processing
    // time (a perf metric elsewhere), not clip length -- there is no
    // shortcut around actually reading the file. preload="metadata" plus an
    // explicit load() call is that mechanism: it fetches just the header via
    // a small range request the moment src is set, well before Play.
    const job: JobRecord = {
      content_hash: "long-hash",
      status: "done",
      audio_url: "https://example.test/long.wav",
    };
    const api = {
      getJob: async () => job,
    } as unknown as AuritusApiClient;
    const loadCalls: HTMLMediaElement[] = [];
    vi.spyOn(HTMLMediaElement.prototype, "load").mockImplementation(
      function (this: HTMLMediaElement) {
        loadCalls.push(this);
      },
    );

    const host = document.createElement("div");
    document.body.appendChild(host);
    mountPlayer({
      host,
      api,
      contentHash: "long-hash",
      name: "Long Article",
      byline: "Author",
      pollIntervalMs: 15,
    });

    const audio = host.shadowRoot?.querySelector("audio") as HTMLAudioElement;
    expect(audio.preload).toBe("metadata");

    await vi.waitFor(() => {
      expect(audio.src).toContain("long.wav");
    });
    expect(loadCalls).toContain(audio);
  });
});

describe("mountPlayer native controls handoff", () => {
  afterEach(() => {
    document.body.replaceChildren();
    vi.restoreAllMocks();
  });

  it("reveals native <audio controls> and hides the pending UI once the job is already done", async () => {
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

    const pendingEl = host.shadowRoot?.querySelector(
      ".auritus-pending",
    ) as HTMLDivElement;
    const audio = host.shadowRoot?.querySelector("audio") as HTMLAudioElement;

    await vi.waitFor(() => {
      expect(audio.src).toContain("speech.wav");
    });
    expect(pendingEl.hidden).toBe(true);
    expect(audio.hidden).toBe(false);
    expect(audio.hasAttribute("controls")).toBe(true);
  });

  it("rewinds a finished clip on ended, so native controls can replay it", () => {
    const job: JobRecord = {
      content_hash: "rewind-hash",
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
      contentHash: "rewind-hash",
      name: "Test Title",
      byline: "Test Author",
      pollIntervalMs: 15,
    });

    const audio = host.shadowRoot?.querySelector("audio") as HTMLAudioElement;
    Object.defineProperty(audio, "duration", {
      value: 30,
      writable: true,
      configurable: true,
    });
    Object.defineProperty(audio, "currentTime", {
      value: 30,
      writable: true,
      configurable: true,
    });
    Object.defineProperty(audio, "ended", {
      value: true,
      writable: true,
      configurable: true,
    });
    audio.dispatchEvent(new Event("ended"));
    expect(audio.currentTime).toBe(0);
  });

  it("shows an error and hides the pending UI when generation fails", async () => {
    const job: JobRecord = { content_hash: "failed-hash", status: "failed" };
    const api = {
      getJob: async () => job,
    } as unknown as AuritusApiClient;

    const host = document.createElement("div");
    document.body.appendChild(host);
    mountPlayer({
      host,
      api,
      contentHash: "failed-hash",
      name: "Test Title",
      byline: "Test Author",
      pollIntervalMs: 15,
    });

    const pendingEl = host.shadowRoot?.querySelector(
      ".auritus-pending",
    ) as HTMLDivElement;
    const errorEl = host.shadowRoot?.querySelector(
      ".auritus-error",
    ) as HTMLParagraphElement;
    const audio = host.shadowRoot?.querySelector("audio") as HTMLAudioElement;

    await vi.waitFor(() => {
      expect(errorEl.hidden).toBe(false);
    });
    expect(pendingEl.hidden).toBe(true);
    expect(audio.hidden).toBe(true);
  });
});
