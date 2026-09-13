import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { JSDOM } from "jsdom";
import { boot } from "../src/index.js";

function pendingResponse(): Response {
  return {
    ok: true,
    json: async () => ({ status: "pending", content_hash: "abc" }),
    text: async () => "",
  } as Response;
}

describe("overlapping boot", () => {
  let dom: JSDOM;

  beforeEach(() => {
    dom = new JSDOM(
      `<!DOCTYPE html><html><body>
        <div class="auritus-player-host"></div>
        <article class="example-article"><p>Hello speech.</p></article>
        <div
          data-auritus-site-key="demo-site-key"
          data-auritus-api="https://api.test"
          data-auritus-root=".example-article"
          data-auritus-player-host=".auritus-player-host"
        ></div>
      </body></html>`,
      { url: "https://aurit.us/examples/basic" },
    );
    globalThis.document = dom.window.document;
    HTMLMediaElement.prototype.pause = function pause() {
      return undefined;
    };
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("keeps player controls when a stale boot finishes after a newer boot", async () => {
    let createCalls = 0;
    const fetchImpl = vi.fn(async (_url: string, init?: RequestInit) => {
      if (init?.method === "POST") {
        createCalls += 1;
        const delay = createCalls === 1 ? 80 : 10;
        await new Promise((resolve) => {
          setTimeout(resolve, delay);
        });
        return pendingResponse();
      }
      return pendingResponse();
    });
    vi.stubGlobal("fetch", fetchImpl);

    const element = document.querySelector(
      "[data-auritus-site-key]",
    ) as HTMLElement;
    const first = boot({ element });
    const second = boot({ element });
    await Promise.all([first, second]);

    const hosts = document.querySelectorAll(".auritus-root");
    expect(hosts.length).toBe(1);
    const play = hosts[0]?.shadowRoot?.querySelector(".auritus-play");
    expect(play).toBeTruthy();
  });
});
