import { expect, test, type Page } from "@playwright/test";

type JobPostBody = {
  text?: string;
  tts_backend?: string;
  voice_id?: string;
};

async function waitForJobPost(page: Page) {
  return page.waitForRequest(
    (req) =>
      req.method() === "POST" && new URL(req.url()).pathname.endsWith("/jobs"),
    { timeout: 120_000 },
  );
}

test("basic example shows player chrome without JavaScript", async ({
  browser,
}) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto("/examples/basic");
  await expect(page.getByText("Loading player")).toBeVisible();
  const hostBox = await page.locator(".auritus-player-host").boundingBox();
  const articleBox = await page.locator(".example-article").boundingBox();
  expect(hostBox).toBeTruthy();
  expect(articleBox).toBeTruthy();
  expect(hostBox!.y).toBeLessThan(articleBox!.y);
  await context.close();
});

test("basic example loads and shows player container", async ({ page }) => {
  await page.goto("/examples/basic");
  await expect(page.locator("[data-auritus-site-key]")).toBeAttached();
  const host = page.locator(".auritus-player-host");
  await expect(host).toBeVisible();
  await expect(page.locator(".auritus-root")).toBeVisible({ timeout: 15_000 });
  const hostBox = await host.boundingBox();
  const articleBox = await page.locator(".example-article").boundingBox();
  expect(hostBox).toBeTruthy();
  expect(articleBox).toBeTruthy();
  expect(hostBox!.height).toBeGreaterThan(40);
  expect(hostBox!.y).toBeLessThan(articleBox!.y);
});

test("player chrome mounts before POST /jobs returns", async ({ page }) => {
  await page.route("**/jobs", async (route) => {
    if (route.request().method() === "POST") {
      await new Promise((resolve) => {
        setTimeout(resolve, 4000);
      });
    }
    await route.continue();
  });
  await page.goto("/examples/basic");
  await page.waitForFunction(
    () => {
      const host = document.querySelector(".auritus-root");
      const play = host?.shadowRoot?.querySelector(".auritus-play");
      return Boolean(play);
    },
    { timeout: 3000 },
  );
});

test("themed example applies CSS variables", async ({ page }) => {
  await page.goto("/examples/themed");
  await expect(
    page.locator('[style*="--auritus-accent"]').first(),
  ).toBeVisible();
});

test("ignore example has data-auritus-ignore on nav", async ({ page }) => {
  await page.goto("/examples/ignore");
  await expect(page.locator("nav[data-auritus-ignore]")).toBeAttached();
});

test("embed script is loaded", async ({ page }) => {
  await page.goto("/examples/basic");
  await expect(page.locator('script[src*="embed.js"]')).toBeAttached();
});

test("basic example plays Kokoro speech scoped to article", async ({
  page,
}) => {
  test.setTimeout(180_000);

  const createJobRequest = waitForJobPost(page);
  await page.goto("/examples/basic");

  const jobRequest = await createJobRequest;
  const body = jobRequest.postDataJSON() as JobPostBody;
  expect(body.tts_backend).toBe("kokoro");
  expect(body.voice_id).toBe("af_heart");
  expect(body.text).toContain("Four score and seven years ago");
  expect(body.text).toContain("Now we are engaged in a great civil war");
  expect(body.text).not.toContain("Examples");
  expect(body.text).not.toContain("__next_f");

  const config = page.locator("[data-auritus-site-key]").first();
  await expect(config).toHaveAttribute("data-auritus-tts-backend", "kokoro");
  await expect(config).toHaveAttribute("data-auritus-root", ".example-article");

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

  const durationSeconds = await page.locator(".auritus-root").evaluate(
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

  expect(durationSeconds).toBeGreaterThanOrEqual(8);
});

test("themed example posts a distinct Austen excerpt", async ({ page }) => {
  test.setTimeout(180_000);
  const createJobRequest = waitForJobPost(page);
  await page.goto("/examples/themed");
  const body = (await createJobRequest).postDataJSON() as JobPostBody;
  expect(body.tts_backend).toBe("kokoro");
  expect(body.text).toContain("It is a truth universally acknowledged");
  expect(body.text).toContain("However little known the feelings");
  expect(body.text).not.toContain("Four score and seven years ago");
});

test("Qwen example posts a distinct Darwin excerpt", async ({ page }) => {
  test.setTimeout(180_000);
  const createJobRequest = waitForJobPost(page);
  await page.goto("/examples/qwen");
  const body = (await createJobRequest).postDataJSON() as JobPostBody;
  expect(body.tts_backend).toBe("qwen");
  expect(body.voice_id).toBe("Ryan");
  expect(body.text).toContain("When on board H.M.S.");
  expect(body.text).not.toContain("Four score and seven years ago");
});

test("ignore example posts Kokoro job without ignored paragraph", async ({
  page,
}) => {
  test.setTimeout(180_000);

  const createJobRequest = waitForJobPost(page);
  await page.goto("/examples/ignore");

  const body = (await createJobRequest).postDataJSON() as JobPostBody;
  expect(body.tts_backend).toBe("kokoro");
  expect(body.voice_id).toBe("af_heart");
  expect(body.text).toContain("The only freedom which deserves the name");
  expect(body.text).not.toContain("This paragraph is ignored");
});

test("client navigation boots a new job for the destination page", async ({
  page,
}) => {
  test.setTimeout(180_000);

  const ignorePost = waitForJobPost(page);
  await page.goto("/examples/ignore");
  const ignoreBody = (await ignorePost).postDataJSON() as JobPostBody;
  expect(ignoreBody.text).toContain("The only freedom which deserves the name");

  const basicPost = waitForJobPost(page);
  await page.getByRole("link", { name: "Basic example" }).click();
  const basicBody = (await basicPost).postDataJSON() as JobPostBody;
  expect(basicBody.text).toContain("Four score and seven years ago");
  expect(basicBody.text).not.toContain(
    "The only freedom which deserves the name",
  );
});
