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
