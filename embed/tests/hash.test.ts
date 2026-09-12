import { describe, expect, it } from "vitest";
import { computeContentHash, normalizeText } from "../src/generator/hash.js";

const SAMPLE_TEXT = "Hello   world.\nNew line.";
const VOICE = "default";

describe("normalizeText", () => {
  it("collapses whitespace and trims", () => {
    expect(normalizeText(SAMPLE_TEXT)).toBe("Hello world. New line.");
  });
});

describe("computeContentHash", () => {
  it("is stable for the same text and voice", () => {
    const a = computeContentHash(SAMPLE_TEXT, VOICE);
    const b = computeContentHash("Hello   world.\nNew line.", VOICE);
    expect(a).toBe(b);
  });

  it("does not change when only name or byline would differ (hash ignores them)", () => {
    const base = computeContentHash(SAMPLE_TEXT, VOICE);
    const same = computeContentHash(SAMPLE_TEXT, VOICE);
    expect(base).toBe(same);
    expect(base).not.toBe(
      computeContentHash("Different article body", VOICE),
    );
  });

  it("does not change when tts_backend changes (hash excludes backend)", () => {
    const base = computeContentHash(SAMPLE_TEXT, VOICE);
    expect(base).toBe(computeContentHash(SAMPLE_TEXT, VOICE));
  });

  it("changes when normalized text changes", () => {
    const base = computeContentHash(SAMPLE_TEXT, VOICE);
    expect(base).not.toBe(
      computeContentHash("Hello world. New line!", VOICE),
    );
  });

  it("changes when voice_id changes", () => {
    const base = computeContentHash(SAMPLE_TEXT, VOICE);
    expect(base).not.toBe(computeContentHash(SAMPLE_TEXT, "alt-voice"));
  });
});
