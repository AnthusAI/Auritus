import { expect, test } from "@playwright/test";

test("basic example loads and shows player container", async ({ page }) => {
  await page.goto("/examples/basic");
  await expect(page.locator("[data-auritus-site-key]")).toBeVisible();
});

test("themed example applies CSS variables", async ({ page }) => {
  await page.goto("/examples/themed");
  await expect(
    page.locator('[style*="--auritus-accent"]').first(),
  ).toBeVisible();
});

test("ignore example has data-auritus-ignore on nav", async ({ page }) => {
  await page.goto("/examples/ignore");
  await expect(page.locator("[data-auritus-ignore]")).toBeAttached();
});

test("embed script is loaded", async ({ page }) => {
  await page.goto("/examples/basic");
  await expect(page.locator('script[src*="embed.js"]')).toBeAttached();
});

test("basic example plays Kokoro speech scoped to article", async ({
  page,
}) => {
  test.setTimeout(180_000);

  const createJobRequest = page.waitForRequest(
    (req) =>
      req.method() === "POST" && new URL(req.url()).pathname.endsWith("/jobs"),
    { timeout: 120_000 },
  );

  await page.goto("/examples/basic");

  const jobRequest = await createJobRequest;
  const body = jobRequest.postDataJSON() as {
    text?: string;
    tts_backend?: string;
  };
  expect(body.tts_backend).toBe("kokoro");
  expect(body.text).toContain("Basic narration example");
  expect(body.text).not.toContain("Examples");
  expect(body.text).not.toContain("__next_f");

  const embedScript = page.locator('script[src*="embed.js"]');
  await expect(embedScript).toHaveAttribute(
    "data-auritus-tts-backend",
    "kokoro",
  );
  await expect(embedScript).toHaveAttribute(
    "data-auritus-root",
    ".example-article",
  );

  await expect(page.locator(".auritus-root")).toBeAttached();

  await page.waitForFunction(
    () => {
      const host = document.querySelector(".auritus-root");
      const shadow = host?.shadowRoot;
      const playBtn = shadow?.querySelector(
        ".auritus-play",
      ) as HTMLButtonElement | null;
      return Boolean(playBtn && !playBtn.disabled);
    },
    { timeout: 120_000 },
  );

  const playVisibleInShadow = await page
    .locator(".auritus-root")
    .evaluate((host) => {
      const shadow = host.shadowRoot;
      const playBtn = shadow?.querySelector(".auritus-play");
      return playBtn instanceof HTMLButtonElement && !playBtn.disabled;
    });
  expect(playVisibleInShadow).toBe(true);

  const durationSeconds = await page
    .locator(".auritus-root")
    .evaluate(
      async (host) => {
        const audio = host.shadowRoot?.querySelector("audio");
        if (!audio?.src) {
          return 0;
        }
        if (Number.isFinite(audio.duration) && audio.duration > 0) {
          return audio.duration;
        }
        await new Promise<void>((resolve, reject) => {
          audio.addEventListener("loadedmetadata", () => resolve(), {
            once: true,
          });
          audio.addEventListener(
            "error",
            () => reject(new Error("audio metadata load failed")),
            { once: true },
          );
          audio.load();
        });
        return audio.duration;
      },
      { timeout: 120_000 },
    );

  expect(durationSeconds).toBeGreaterThanOrEqual(4);
});
