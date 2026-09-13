import { describe, expect, it } from "vitest";
import { computeContentHash, normalizeText } from "../src/generator/hash.js";

const SAMPLE_TEXT = "Hello   world.\nNew line.";
const VOICE = "af_heart";

describe("normalizeText", () => {
  it("collapses whitespace and trims", () => {
    expect(normalizeText(SAMPLE_TEXT)).toBe("Hello world. New line.");
  });
});

describe("computeContentHash", () => {
  it("is stable for the same text, voice, and backend", () => {
    const a = computeContentHash(SAMPLE_TEXT, VOICE, "kokoro");
    const b = computeContentHash("Hello   world.\nNew line.", VOICE, "kokoro");
    expect(a).toBe(b);
  });

  it("does not change when only name or byline would differ (hash ignores them)", () => {
    const base = computeContentHash(SAMPLE_TEXT, VOICE, "kokoro");
    const same = computeContentHash(SAMPLE_TEXT, VOICE, "kokoro");
    expect(base).toBe(same);
    expect(base).not.toBe(
      computeContentHash("Different article body", VOICE, "kokoro"),
    );
  });

  it("matches the live home-page Kokoro pitch hash", () => {
    const pitch =
      "Press play. What you hear is this page reading itself. Auritus turns any article into audio on demand, from a single script tag — no pre-recording, no studio, no per-article cost. You choose the voice model. You decide where the text goes. Your own GPU does the work, and AWS picks up the slack when it cannot. It's open source, and every article on your site can speak, with the choices that matter still yours.";
    expect(computeContentHash(pitch, VOICE, "kokoro")).toBe("2caf28aa");
  });

  it("changes when tts_backend changes", () => {
    const base = computeContentHash(SAMPLE_TEXT, VOICE, "kokoro");
    expect(base).not.toBe(computeContentHash(SAMPLE_TEXT, VOICE, "qwen"));
  });

  it("changes when normalized text changes", () => {
    const base = computeContentHash(SAMPLE_TEXT, VOICE, "kokoro");
    expect(base).not.toBe(
      computeContentHash("Hello world. New line!", VOICE, "kokoro"),
    );
  });

  it("changes when voice_id changes", () => {
    const base = computeContentHash(SAMPLE_TEXT, VOICE, "kokoro");
    expect(base).not.toBe(
      computeContentHash(SAMPLE_TEXT, "alt-voice", "kokoro"),
    );
  });
});
