import { defineConfig, devices } from "@playwright/test";

// Local dev/CI default; set AURITUS_E2E_BASE_URL to target another host (e.g. staging).
const baseURL = process.env.AURITUS_E2E_BASE_URL || "http://localhost:3000";

export default defineConfig({
  testDir: "./tests",
  testMatch: "acceptance.spec.ts",
  fullyParallel: !process.env.CI,
  workers: process.env.CI ? 1 : undefined,
  use: {
    baseURL,
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: baseURL.includes("localhost")
    ? {
        command: "npm run dev",
        timeout: process.env.CI ? 120_000 : 30_000,
        url: baseURL,
        reuseExistingServer: !process.env.CI,
      }
    : undefined,
});
