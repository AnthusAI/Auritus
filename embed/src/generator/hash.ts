/** Pause marker inserted for elements with data-auritus-break. */
export const AURITUS_BREAK_MARKER = "[[auritus:break]]";

/**
 * Normalize TTS input for hashing: NFC, trim, collapse internal whitespace.
 */
export function normalizeText(text: string): string {
  return text.normalize("NFC").replace(/\s+/g, " ").trim();
}

const FNV_OFFSET_BASIS = 0x811c9dc5;
const FNV_PRIME = 0x01000193;

function fnv1a32(input: string): string {
  let hash = FNV_OFFSET_BASIS;
  for (let i = 0; i < input.length; i++) {
    hash ^= input.charCodeAt(i);
    hash = Math.imul(hash, FNV_PRIME);
  }
  return (hash >>> 0).toString(16).padStart(8, "0");
}

/**
 * Stable content hash from normalized text, voice, and backend only.
 * Name and byline are intentionally excluded.
 */
export function computeContentHash(
  text: string,
  voiceId: string,
  ttsBackend: string,
): string {
  const payload = `${normalizeText(text)}\0${voiceId}\0${ttsBackend}`;
  return fnv1a32(payload);
}
