/**
 * Read display metadata from the embed config element, with document fallbacks.
 */
export function readEmbedMetadata(element: HTMLElement): {
  name: string;
  byline: string;
} {
  const name =
    element.getAttribute("data-auritus-name")?.trim() ||
    document.title.trim() ||
    "";
  const byline =
    element.getAttribute("data-auritus-byline")?.trim() ||
    location.hostname ||
    "";
  return { name, byline };
}
