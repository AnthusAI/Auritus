import { expect, test, type Page } from "@playwright/test";

type JobPostBody = {
  text?: string;
  tts_backend?: string;
  voice_id?: string;
  content_hash?: string;
};

async function waitForJobPost(page: Page) {
  return page.waitForRequest(
    (req) =>
      req.method() === "POST" && new URL(req.url()).pathname.endsWith("/jobs"),
    { timeout: 120_000 },
  );
}

async function waitForPlayableClip(page: Page) {
  await page.waitForFunction(
    () => {
      const host = document.querySelector(".auritus-root");
      const playBtn = host?.shadowRoot?.querySelector(
        ".auritus-play",
      ) as HTMLButtonElement | null;
      const audio = host?.shadowRoot?.querySelector("audio");
      return Boolean(playBtn && audio?.src);
    },
    { timeout: 120_000 },
  );
}

async function clipDurationSeconds(page: Page): Promise<number> {
  return page.locator(".auritus-root").evaluate(
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
}

test("basic example shows player chrome without JavaScript", async ({
  browser,
}) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto("/examples/basic");
  await expect(page.getByRole("button", { name: "Play" })).toBeVisible();
  await expect(page.getByText("Loading player")).toHaveCount(0);
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

test("landing page posts the Kokoro product pitch", async ({ page }) => {
  test.setTimeout(180_000);
  const createJobRequest = waitForJobPost(page);
  await page.goto("/");
  const body = (await createJobRequest).postDataJSON() as JobPostBody;
  expect(body.tts_backend).toBe("kokoro");
  expect(body.voice_id).toBe("af_heart");
  expect(body.content_hash).toBe("2caf28aa");
  expect(body.text).toContain("Press play");
  expect(body.text).toContain("What you hear is this page reading itself");
  expect(body.text).not.toContain("Narrated by Auritus with Kokoro");
  await expect(page.locator(".auritus-root")).toBeVisible({ timeout: 15_000 });
  await waitForPlayableClip(page);
  const durationSeconds = await clipDurationSeconds(page);
  expect(durationSeconds).toBeGreaterThanOrEqual(20);
});

test("landing page explains the local-first cloud fallback", async ({
  page,
}) => {
  await page.goto("/");

  await expect(
    page.getByRole("heading", {
      name: "Let every page speak.",
    }),
  ).toBeVisible();
  // The fallback diagram must still say the local worker claims first and that
  // AWS only steps in when nothing claims before the timeout.
  await expect(
    page.getByRole("img", { name: /Your own GPU claims it first/i }),
  ).toBeVisible();
  await expect(
    page.getByRole("img", {
      name: /only if no claim arrives before the timeout/i,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: /explore deployment options/i }),
  ).toHaveAttribute("href", "/docs/architecture");
  await expect(page.locator(".choice-number")).toHaveCount(0);
});

test("landing page does not overflow a narrow viewport", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");

  const dimensions = await page.evaluate(() => ({
    clientWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }));
  expect(dimensions.scrollWidth).toBeLessThanOrEqual(dimensions.clientWidth);
});

test("architecture documentation showcases identity options", async ({
  page,
}) => {
  await page.goto("/docs/architecture");

  await expect(
    page.getByRole("heading", {
      name: "Choose the login experience your team needs.",
    }),
  ).toBeVisible();
  await expect(page.getByText("AWS IAM Identity Center")).toBeVisible();
  await expect(page.getByText("Supported (SAML 2.0 / SSO)")).toBeVisible();
});

test("security page documents unattended worker auth and is reachable from the home nav", async ({
  page,
}) => {
  await page.goto("/docs/security");
  await expect(
    page.getByRole("heading", {
      name: /The worker never holds a key worth stealing/i,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: /Rotation happens on its own/i }),
  ).toBeVisible();

  // All three identity options are presented, each with its real status.
  for (const name of [
    /Native Cognito users/i,
    /Google Workspace/i,
    /AWS IAM Identity Center or any SAML provider/i,
  ]) {
    await expect(page.getByRole("heading", { name })).toBeVisible();
  }

  // The page must keep stating what is not enforced yet, not just the promises.
  await expect(
    page.getByRole("heading", { name: /What is not true yet/i }),
  ).toBeVisible();
  await expect(
    page.getByText(/does not verify token signatures yet/i),
  ).toBeVisible();

  await expect(
    page.getByRole("link", { name: /Configure your own stack/i }),
  ).toHaveAttribute("href", "/docs/self-hosting");

  await page.goto("/");
  await expect(
    page.getByRole("link", { name: "Security", exact: true }),
  ).toHaveAttribute("href", "/docs/security");
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
  expect(body.text).not.toContain("This page speaks that excerpt");

  const config = page.locator("[data-auritus-site-key]").first();
  await expect(config).toHaveAttribute("data-auritus-tts-backend", "kokoro");
  await expect(config).toHaveAttribute("data-auritus-root", ".example-article");

  await expect(page.locator(".auritus-root")).toBeAttached();

  await waitForPlayableClip(page);
  const durationSeconds = await clipDurationSeconds(page);
  expect(durationSeconds).toBeGreaterThanOrEqual(8);
});

test("Play while waiting starts Kokoro when audio arrives", async ({
  page,
}) => {
  test.setTimeout(180_000);
  let releaseJobGets: () => void = () => {};
  const jobGetsReady = new Promise<void>((resolve) => {
    releaseJobGets = resolve;
  });
  await page.route("**/jobs/**", async (route) => {
    const request = route.request();
    const pathname = new URL(request.url()).pathname;
    const isJobRecordGet =
      request.method() === "GET" && /\/jobs\/[0-9a-f]+$/i.test(pathname);
    if (!isJobRecordGet) {
      await route.continue();
      return;
    }
    await jobGetsReady;
    await route.continue();
  });
  await page.goto("/examples/basic");
  await page.waitForFunction(() => {
    const play = document
      .querySelector(".auritus-root")
      ?.shadowRoot?.querySelector(".auritus-play");
    return Boolean(play);
  });
  await page.locator(".auritus-root").evaluate((host) => {
    const playBtn = host.shadowRoot?.querySelector(
      ".auritus-play",
    ) as HTMLButtonElement | null;
    playBtn?.click();
  });
  const waitingStatus = await page.locator(".auritus-root").evaluate((host) => {
    return host.shadowRoot?.querySelector(".auritus-status")?.textContent ?? "";
  });
  expect(waitingStatus).toContain("Starting when ready");
  releaseJobGets();
  await page.waitForFunction(
    () => {
      const host = document.querySelector(".auritus-root");
      const audio = host?.shadowRoot?.querySelector("audio");
      const playBtn = host?.shadowRoot?.querySelector(
        ".auritus-play",
      ) as HTMLButtonElement | null;
      return Boolean(
        audio &&
        !audio.paused &&
        playBtn?.getAttribute("aria-label") === "Pause",
      );
    },
    { timeout: 120_000 },
  );
});

test("Play after the clip ends starts Kokoro speech from the beginning", async ({
  page,
}) => {
  test.setTimeout(180_000);
  await page.goto("/examples/basic");
  await page.waitForFunction(
    () => {
      const host = document.querySelector(".auritus-root");
      const playBtn = host?.shadowRoot?.querySelector(
        ".auritus-play",
      ) as HTMLButtonElement | null;
      const audio = host?.shadowRoot?.querySelector("audio");
      return Boolean(playBtn && !playBtn.disabled && audio?.src);
    },
    { timeout: 120_000 },
  );

  await page.locator(".auritus-root").evaluate(async (host) => {
    const audio = host.shadowRoot?.querySelector("audio");
    if (!audio) {
      throw new Error("player audio missing");
    }
    if (!Number.isFinite(audio.duration) || audio.duration <= 0) {
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
    }
    audio.pause();
    audio.currentTime = audio.duration;
  });

  await page.getByRole("button", { name: "Play", disabled: false }).click();

  await page.waitForFunction(
    () => {
      const host = document.querySelector(".auritus-root");
      const audio = host?.shadowRoot?.querySelector("audio");
      const playBtn = host?.shadowRoot?.querySelector(
        ".auritus-play",
      ) as HTMLButtonElement | null;
      return Boolean(
        audio &&
        playBtn &&
        !audio.paused &&
        audio.currentTime > 0 &&
        audio.currentTime < 8 &&
        playBtn.getAttribute("aria-label") === "Pause",
      );
    },
    { timeout: 15_000 },
  );
});

test("themed example posts the same Gettysburg excerpt with Kokoro", async ({
  page,
}) => {
  test.setTimeout(180_000);
  const createJobRequest = waitForJobPost(page);
  await page.goto("/examples/themed");
  const body = (await createJobRequest).postDataJSON() as JobPostBody;
  expect(body.tts_backend).toBe("kokoro");
  expect(body.text).toContain("Four score and seven years ago");
  expect(body.text).toContain("Now we are engaged in a great civil war");
  expect(body.text).not.toContain("This page speaks that excerpt");
  await waitForPlayableClip(page);
  expect(await clipDurationSeconds(page)).toBeGreaterThanOrEqual(8);
});

test("Qwen example posts the same Gettysburg excerpt with Qwen", async ({
  page,
}) => {
  test.setTimeout(180_000);
  const createJobRequest = waitForJobPost(page);
  await page.goto("/examples/qwen");
  const body = (await createJobRequest).postDataJSON() as JobPostBody;
  expect(body.tts_backend).toBe("qwen");
  expect(body.voice_id).toBe("Ryan");
  expect(body.text).toContain("Four score and seven years ago");
  expect(body.text).toContain("Now we are engaged in a great civil war");
  expect(body.text).not.toContain("When on board H.M.S.");
  expect(body.text).not.toContain("This page speaks that excerpt");
  await waitForPlayableClip(page);
  expect(await clipDurationSeconds(page)).toBeGreaterThanOrEqual(20);
});

test("F5 example posts the same Gettysburg excerpt with F5", async ({
  page,
}) => {
  test.setTimeout(180_000);
  const createJobRequest = waitForJobPost(page);
  await page.goto("/examples/f5");
  const body = (await createJobRequest).postDataJSON() as JobPostBody;
  expect(body.tts_backend).toBe("f5");
  expect(body.voice_id).toBe("default");
  expect(body.text).toContain("Four score and seven years ago");
  expect(body.text).toContain("Now we are engaged in a great civil war");
  expect(body.text).not.toContain("This page speaks that excerpt");
});

test("Chatterbox example posts the same Gettysburg excerpt with Chatterbox", async ({
  page,
}) => {
  test.setTimeout(180_000);
  const createJobRequest = waitForJobPost(page);
  await page.goto("/examples/chatterbox");
  const body = (await createJobRequest).postDataJSON() as JobPostBody;
  expect(body.tts_backend).toBe("chatterbox");
  expect(body.voice_id).toBe("default");
  expect(body.text).toContain("Four score and seven years ago");
  expect(body.text).toContain("Now we are engaged in a great civil war");
  expect(body.text).not.toContain("This page speaks that excerpt");
});

test("Kokoro, Qwen, and F5 examples POST the same spoken text", async ({
  browser,
}) => {
  test.setTimeout(180_000);
  const kokoroPage = await browser.newPage();
  const qwenPage = await browser.newPage();
  const f5Page = await browser.newPage();
  const kokoroPost = waitForJobPost(kokoroPage);
  const qwenPost = waitForJobPost(qwenPage);
  const f5Post = waitForJobPost(f5Page);
  await Promise.all([
    kokoroPage.goto("/examples/basic"),
    qwenPage.goto("/examples/qwen"),
    f5Page.goto("/examples/f5"),
  ]);
  const kokoroBody = (await kokoroPost).postDataJSON() as JobPostBody;
  const qwenBody = (await qwenPost).postDataJSON() as JobPostBody;
  const f5Body = (await f5Post).postDataJSON() as JobPostBody;
  expect(kokoroBody.tts_backend).toBe("kokoro");
  expect(qwenBody.tts_backend).toBe("qwen");
  expect(f5Body.tts_backend).toBe("f5");
  expect(kokoroBody.text).toBe(qwenBody.text);
  expect(f5Body.text).toBe(kokoroBody.text);
  expect(kokoroBody.content_hash).not.toBe(qwenBody.content_hash);
  expect(f5Body.content_hash).not.toBe(kokoroBody.content_hash);
  await kokoroPage.close();
  await qwenPage.close();
  await f5Page.close();
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
  await waitForPlayableClip(page);
  expect(await clipDurationSeconds(page)).toBeGreaterThanOrEqual(8);
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

test("ModelCompareNav renders all models and active states", async ({
  page,
}) => {
  await page.goto("/examples/chatterbox");

  // Check topbar
  await expect(page.locator(".model-nav-back")).toHaveText("← All Examples");
  await expect(page.locator(".model-nav-docs")).toHaveText("Usage →");

  // Check stepper
  const prevBtn = page.locator(".model-stepper-btn").first();
  const nextBtn = page.locator(".model-stepper-btn").last();
  await expect(prevBtn).toHaveText("‹ Higgs-v3");
  await expect(nextBtn).toHaveText("Kokoro-82M ›");
  await expect(page.locator(".model-stepper-indicator")).toHaveText("5 of 5");

  // Check model pills
  const pills = page.locator(".model-pill");
  await expect(pills).toHaveCount(5);

  const activePill = page.locator(".model-pill.active");
  await expect(activePill).toContainText("Chatterbox");
  await expect(activePill).toContainText("520M");

  // Check spec strip
  const specStrip = page.locator(".model-spec-strip");
  await expect(specStrip).toBeVisible();
  await expect(specStrip).toContainText("LLaMA-520M + Matcha-TTS Flow");
  await expect(specStrip).toContainText("Resemble AI");
  await expect(specStrip).toContainText("24 kHz Mono");
  await expect(specStrip).toContainText("Apache-2.0");

  // Click Prev model (Higgs)
  await prevBtn.click();
  await expect(page).toHaveURL("/examples/higgs");
  await expect(page.locator(".model-pill.active")).toContainText("Higgs-v3");
  await expect(page.locator(".model-stepper-indicator")).toHaveText("4 of 5");
});

test("ModelCompareNav dropdown is present for responsive viewports", async ({
  page,
}) => {
  await page.setViewportSize({ width: 480, height: 800 });
  await page.goto("/examples/basic");

  const dropdown = page.locator(".model-select-dropdown");
  await expect(dropdown).toBeVisible();
  await expect(dropdown).toHaveValue("/examples/basic");

  // Change dropdown to Chatterbox
  await dropdown.selectOption("/examples/chatterbox");
  await expect(page).toHaveURL("/examples/chatterbox");
  await expect(dropdown).toHaveValue("/examples/chatterbox");
});

