import { afterEach, describe, expect, it, vi } from "vitest";
import type { AuritusApiClient, JobRecord } from "../src/api.js";
import { mountPlayer, rewindIfEnded } from "../src/player/index.js";

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
    } as AuritusApiClient;
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
