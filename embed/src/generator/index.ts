import {
  AURITUS_BREAK_MARKER,
  AURITUS_VOICE_RESET_MARKER,
  formatVoiceMarker,
  normalizeText,
} from "./hash.js";

export {
  AURITUS_BREAK_MARKER,
  AURITUS_VOICE_RESET_MARKER,
  formatVoiceMarker,
  normalizeText,
  computeContentHash,
} from "./hash.js";
export { readEmbedMetadata } from "./metadata.js";

const BUILTIN_IGNORE_SELECTOR = "[data-auritus-ignore]";

/**
 * Block-level tags that get an automatic pause marker after their content,
 * with no markup changes required on the host page. A heading read flush
 * against the paragraph that follows it (or one paragraph flush against
 * the next) reads as a run-on; ordinary semantic HTML already marks these
 * boundaries, so the generator can insert the same data-auritus-break
 * behavior authors would otherwise have to add by hand to every element.
 */
const AUTO_BREAK_TAGS = new Set([
  "h1",
  "h2",
  "h3",
  "h4",
  "h5",
  "h6",
  "p",
  "li",
  "blockquote",
  "figcaption",
]);

export interface GeneratorConfig {
  /** CSS selector for the content root; defaults to document.body. */
  root?: string | Element;
  /** Additional CSS selectors for subtrees to skip. */
  ignoreSelectors?: string[];
}

export interface GeneratorResult {
  text: string;
}

function resolveRoot(root?: string | Element): Element {
  if (root instanceof Element) {
    return root;
  }
  if (typeof root === "string" && root.length > 0) {
    const el = document.querySelector(root);
    if (!el) {
      throw new Error(`Auritus generator: root not found: ${root}`);
    }
    return el;
  }
  if (!document.body) {
    throw new Error("Auritus generator: document.body is not available");
  }
  return document.body;
}

function elementMatchesIgnore(el: Element, selectors: string[]): boolean {
  if (el.hasAttribute("data-auritus-ignore")) {
    return true;
  }
  for (const selector of selectors) {
    if (selector && el.matches(selector)) {
      return true;
    }
  }
  return false;
}

function walkNode(
  node: Node,
  ignoreSelectors: string[],
  parts: string[],
): void {
  if (node.nodeType === Node.ELEMENT_NODE) {
    const el = node as Element;
    const tag = el.tagName.toLowerCase();
    if (
      tag === "script" ||
      tag === "style" ||
      tag === "noscript" ||
      tag === "template"
    ) {
      return;
    }
    if (elementMatchesIgnore(el, ignoreSelectors)) {
      return;
    }

    const voiceAttr =
      el.getAttribute("data-auritus-voice") ||
      el.getAttribute("data-auritus-voice-id");
    const hasVoice = voiceAttr !== null && voiceAttr.trim().length > 0;
    if (hasVoice) {
      parts.push(formatVoiceMarker(voiceAttr));
    }

    const pronounce = el.getAttribute("data-auritus-pronounce");
    if (pronounce !== null) {
      parts.push(pronounce);
      if (hasVoice) {
        parts.push(AURITUS_VOICE_RESET_MARKER);
      }
      return;
    }

    if (el.hasAttribute("data-auritus-break")) {
      parts.push(AURITUS_BREAK_MARKER);
    }

    for (const child of el.childNodes) {
      walkNode(child, ignoreSelectors, parts);
    }

    if (hasVoice) {
      parts.push(AURITUS_VOICE_RESET_MARKER);
    }

    if (
      AUTO_BREAK_TAGS.has(tag) &&
      parts[parts.length - 1] !== AURITUS_BREAK_MARKER
    ) {
      parts.push(AURITUS_BREAK_MARKER);
    }
    return;
  }

  if (node.nodeType === Node.TEXT_NODE) {
    const value = node.textContent ?? "";
    if (value.length > 0) {
      parts.push(value);
    }
  }
}

/**
 * Walk the page DOM and build the final TTS input string.
 */
export function generateTtsText(config: GeneratorConfig = {}): GeneratorResult {
  const root = resolveRoot(config.root);
  const ignoreSelectors = [
    BUILTIN_IGNORE_SELECTOR,
    ...(config.ignoreSelectors ?? []),
  ];
  const parts: string[] = [];
  walkNode(root, ignoreSelectors, parts);
  const raw = parts.join(" ");
  return { text: normalizeText(raw) };
}
