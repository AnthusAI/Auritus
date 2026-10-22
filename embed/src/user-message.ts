/** What a visitor reads when narration cannot be provided. */
export const NARRATION_UNAVAILABLE_MESSAGE =
  "Narration is unavailable right now. Please try again later.";

/**
 * Report a narration failure for developers (console) and return the calm
 * message a visitor should see. Raw API errors such as
 * `Auritus POST /jobs failed: 400 {...}` never reach the page.
 */
export function visitorMessage(err: unknown): string {
  const detail = err instanceof Error ? err.message : String(err);
  console.warn(`Auritus: ${detail}`);
  return NARRATION_UNAVAILABLE_MESSAGE;
}
