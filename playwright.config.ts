import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: process.env.BASE_URL || "http://localhost:8000",
    trace: "on-first-retry",
    video: "off",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: process.env.NO_WEBSERVER
    ? undefined
    : {
        command: "cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000",
        url: "http://localhost:8000/api/health",
        reuseExistingServer: true,
        timeout: 30000,
      },
});
