/** Break marker inserted for block elements or data-auritus-break. */
export const AURITUS_BREAK_MARKER = "[[auritus:break]]";

/** Pause marker inserted for elements with data-auritus-pause. */
export const AURITUS_PAUSE_MARKER = "[[auritus:pause]]";

/** Reset marker inserted after elements with data-auritus-voice. */
export const AURITUS_VOICE_RESET_MARKER = "[[auritus:voice:reset]]";

/** Format an inline voice marker for a given voice ID. */
export function formatVoiceMarker(voiceId: string): string {
  return `[[auritus:voice:${voiceId.trim()}]]`;
}

/**
 * Normalize TTS input for hashing: NFC, trim, collapse internal whitespace.
 */
export function normalizeText(text: string): string {
  return text.normalize("NFC").replace(/\s+/g, " ").trim();
}

/**
 * Canonical content hash: SHA-256 (hex) of normalized text, voice ID, and TTS
 * backend joined by NUL characters. The API computes the same value and
 * rejects job creation whose hash does not match.
 * Name and byline are cosmetics and must not affect the hash.
 */
export async function computeContentHash(
  text: string,
  voiceId: string,
  ttsBackend: string,
): Promise<string> {
  const payload = `${normalizeText(text)}\0${voiceId}\0${ttsBackend}`;
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(payload),
  );
  return Array.from(new Uint8Array(digest), (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("");
}
