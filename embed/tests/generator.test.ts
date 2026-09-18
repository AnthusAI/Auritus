import { JSDOM } from "jsdom";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { generateTtsText } from "../src/generator/index.js";
import { AURITUS_BREAK_MARKER } from "../src/generator/hash.js";

describe("generateTtsText", () => {
  let dom: JSDOM;

  beforeEach(() => {
    dom = new JSDOM(
      `<!DOCTYPE html><html><body>
        <article id="content">
          <h1>Title</h1>
          <p>First paragraph.</p>
          <aside data-auritus-ignore>Skip this ad.</aside>
          <p data-auritus-pronounce="Auritus">Wrong spelling</p>
          <p>Before<span data-auritus-break></span>After</p>
        </article>
      </body></html>`,
    );
    globalThis.document = dom.window.document;
  });

  afterEach(() => {
    Reflect.deleteProperty(globalThis, "document");
  });

  it("walks the root, applies ignore and pronounce rules", () => {
    const { text } = generateTtsText({ root: "#content" });
    expect(text).toContain("First paragraph.");
    expect(text).not.toContain("Skip this ad");
    expect(text).toContain("Auritus");
    expect(text).not.toContain("Wrong spelling");
    expect(text).toContain(AURITUS_BREAK_MARKER);
    expect(text).toContain("Before");
    expect(text).toContain("After");
  });

  it("respects additional ignore selectors", () => {
    const { text } = generateTtsText({
      root: "#content",
      ignoreSelectors: ["h1"],
    });
    expect(text).not.toContain("Title");
    expect(text).toContain("First paragraph.");
  });

  it("skips script, style, noscript, and template elements", () => {
    dom = new JSDOM(
      `<!DOCTYPE html><html><body>
        <article id="content">
          <p>Spoken line.</p>
          <script>self.__next_f=self.__next_f||[]</script>
          <style>.x{color:red}</style>
          <noscript>Enable JS</noscript>
          <template><p>Template copy</p></template>
        </article>
      </body></html>`,
    );
    globalThis.document = dom.window.document;
    const { text } = generateTtsText({ root: "#content" });
    expect(text).toContain("Spoken line.");
    expect(text).not.toContain("__next_f");
    expect(text).not.toContain("color:red");
    expect(text).not.toContain("Enable JS");
    expect(text).not.toContain("Template copy");
  });
});

describe("generateTtsText automatic block breaks", () => {
  let dom: JSDOM;

  afterEach(() => {
    Reflect.deleteProperty(globalThis, "document");
  });

  it("inserts a break after headings and paragraphs with no markup required", () => {
    dom = new JSDOM(
      `<!DOCTYPE html><html><body>
        <article id="content">
          <h1>Headline</h1>
          <p>First paragraph.</p>
          <p>Second paragraph.</p>
        </article>
      </body></html>`,
    );
    globalThis.document = dom.window.document;
    const { text } = generateTtsText({ root: "#content" });
    const segments = text
      .split(AURITUS_BREAK_MARKER)
      .map((s) => s.trim())
      .filter(Boolean);
    expect(segments).toEqual([
      "Headline",
      "First paragraph.",
      "Second paragraph.",
    ]);
  });

  it("breaks after list items and blockquotes too", () => {
    dom = new JSDOM(
      `<!DOCTYPE html><html><body>
        <article id="content">
          <ul><li>One</li><li>Two</li></ul>
          <blockquote>A quote.</blockquote>
        </article>
      </body></html>`,
    );
    globalThis.document = dom.window.document;
    const { text } = generateTtsText({ root: "#content" });
    const segments = text
      .split(AURITUS_BREAK_MARKER)
      .map((s) => s.trim())
      .filter(Boolean);
    expect(segments).toEqual(["One", "Two", "A quote."]);
  });

  it("does not double up a break when a manual data-auritus-break sits at a block boundary", () => {
    dom = new JSDOM(
      `<!DOCTYPE html><html><body>
        <article id="content">
          <p>First.<span data-auritus-break></span></p>
          <p>Second.</p>
        </article>
      </body></html>`,
    );
    globalThis.document = dom.window.document;
    const { text } = generateTtsText({ root: "#content" });
    expect(text).not.toContain(
      `${AURITUS_BREAK_MARKER} ${AURITUS_BREAK_MARKER}`,
    );
  });

  it("leaves inline formatting inside a paragraph alone -- only the paragraph boundary gets a break", () => {
    dom = new JSDOM(
      `<!DOCTYPE html><html><body>
        <article id="content">
          <p>Bold <strong>word</strong> and <em>emphasis</em> stay inline.</p>
        </article>
      </body></html>`,
    );
    globalThis.document = dom.window.document;
    const { text } = generateTtsText({ root: "#content" });
    const breakCount = text.split(AURITUS_BREAK_MARKER).length - 1;
    expect(breakCount).toBe(1);
    expect(text).toContain("Bold word and emphasis stay inline.");
  });

  it("extracts fine-grained data-auritus-voice markers and reset markers", () => {
    dom = new JSDOM(
      `<!DOCTYPE html><html><body>
        <article id="content">
          <p>Narrator speaking.</p>
          <blockquote data-auritus-voice="af_bella">Character speaking.</blockquote>
          <p>Narrator resumes.</p>
        </article>
      </body></html>`,
    );
    globalThis.document = dom.window.document;
    const { text } = generateTtsText({ root: "#content" });
    expect(text).toContain("[[auritus:voice:af_bella]]");
    expect(text).toContain("[[auritus:voice:reset]]");
    expect(text).toContain("Character speaking.");
  });
});
