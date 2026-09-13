import { describe, expect, it } from "vitest";
import { rewindIfEnded } from "../src/player/index.js";

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
