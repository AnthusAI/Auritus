import { defineConfig, devices } from "@playwright/test";

// Local dev/CI default; set AURITUS_E2E_BASE_URL to target another host (e.g. staging).
const baseURL = process.env.AURITUS_E2E_BASE_URL || "http://localhost:3000";

export default defineConfig({
  testDir: "./tests",
  testMatch: "acceptance.spec.ts",
  use: {
    baseURL,
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    command: "npm run dev",
    timeout: 30000,
    url: baseURL,
  },
});
