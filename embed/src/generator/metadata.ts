/**
 * Read display metadata from the embed script tag, with document fallbacks.
 */
export function readEmbedMetadata(script: HTMLScriptElement): {
  name: string;
  byline: string;
} {
  const name =
    script.getAttribute("data-auritus-name")?.trim() ||
    document.title.trim() ||
    "";
  const byline =
    script.getAttribute("data-auritus-byline")?.trim() ||
    location.hostname ||
    "";
  return { name, byline };
}
