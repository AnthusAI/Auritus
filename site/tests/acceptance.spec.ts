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
