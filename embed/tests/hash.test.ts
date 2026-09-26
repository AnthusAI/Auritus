import { afterEach, describe, expect, it, vi } from "vitest";
import { computeContentHash, normalizeText } from "../src/generator/hash.js";
import { resolveVoiceId } from "../src/index.js";

const SAMPLE_TEXT = "Hello   world.\nNew line.";
const VOICE = "af_heart";
const UNICODE_SPACES_TEXT = "Cafe\u0301\u00a0\u2003bar\ufeff";

describe("normalizeText", () => {
  it("collapses whitespace and trims", () => {
    expect(normalizeText(SAMPLE_TEXT)).toBe("Hello world. New line.");
  });

  it("composes to NFC and treats Unicode spaces as whitespace", () => {
    expect(normalizeText(UNICODE_SPACES_TEXT)).toBe("Caf\u00e9 bar");
  });
});

describe("computeContentHash", () => {
  it("matches the API's canonical SHA-256 vectors (features/content_hash.feature)", async () => {
    expect(await computeContentHash(SAMPLE_TEXT, VOICE, "kokoro")).toBe(
      "be5ee98501f1984fe1eb93a0ab8e96b3d0f87da538eb37bfb92a702214b0cb6f",
    );
    expect(await computeContentHash(UNICODE_SPACES_TEXT, VOICE, "kokoro")).toBe(
      "6f4ec549d0c26edd736a90e4132de08342f7ededbf34fdef79cd416d011e2824",
    );
  });

  it("is stable for the same normalized text, voice, and backend", async () => {
    expect(await computeContentHash(SAMPLE_TEXT, VOICE, "kokoro")).toBe(
      await computeContentHash("Hello world.  New line. ", VOICE, "kokoro"),
    );
  });

  it("changes when tts_backend changes", async () => {
    expect(await computeContentHash(SAMPLE_TEXT, VOICE, "kokoro")).not.toBe(
      await computeContentHash(SAMPLE_TEXT, VOICE, "qwen"),
    );
  });

  it("changes when normalized text changes", async () => {
    expect(await computeContentHash(SAMPLE_TEXT, VOICE, "kokoro")).not.toBe(
      await computeContentHash("Hello world. New line!", VOICE, "kokoro"),
    );
  });

  it("changes when voice_id changes", async () => {
    expect(await computeContentHash(SAMPLE_TEXT, VOICE, "kokoro")).not.toBe(
      await computeContentHash(SAMPLE_TEXT, "alt-voice", "kokoro"),
    );
  });
});

describe("computeContentHash outside a secure context", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("explains that Web Crypto needs HTTPS", async () => {
    vi.stubGlobal("crypto", {});
    await expect(computeContentHash(SAMPLE_TEXT, VOICE, "kokoro")).rejects.toThrow(
      /secure context \(HTTPS\)/,
    );
  });
});

describe("resolveVoiceId", () => {
  it("resolves missing and 'default' voices to each backend's default like the API", () => {
    expect(resolveVoiceId(undefined, "kokoro")).toBe("af_heart");
    expect(resolveVoiceId("default", "kokoro")).toBe("af_heart");
    expect(resolveVoiceId("default", "qwen")).toBe("Ryan");
    expect(resolveVoiceId("Chelsie", "qwen")).toBe("Ryan");
    expect(resolveVoiceId(undefined, "fish")).toBe("narrator");
    expect(resolveVoiceId("default", "chatterbox")).toBe("narrator");
    expect(resolveVoiceId(undefined, "higgs")).toBe("default");
  });

  it("keeps an explicit voice", () => {
    expect(resolveVoiceId("am_adam", "kokoro")).toBe("am_adam");
    expect(resolveVoiceId("Serena", "qwen")).toBe("Serena");
  });
});
