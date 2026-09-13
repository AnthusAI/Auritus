import { AURITUS_BREAK_MARKER, normalizeText } from "./hash.js";

export { AURITUS_BREAK_MARKER, normalizeText, computeContentHash } from "./hash.js";
export { readEmbedMetadata } from "./metadata.js";

const BUILTIN_IGNORE_SELECTOR = "[data-auritus-ignore]";

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

function walkNode(node: Node, ignoreSelectors: string[], parts: string[]): void {
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

    const pronounce = el.getAttribute("data-auritus-pronounce");
    if (pronounce !== null) {
      parts.push(pronounce);
      return;
    }

    if (el.hasAttribute("data-auritus-break")) {
      parts.push(AURITUS_BREAK_MARKER);
    }

    for (const child of el.childNodes) {
      walkNode(child, ignoreSelectors, parts);
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
