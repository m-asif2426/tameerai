import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 45000,
  expect: {
    timeout: 10000,
  },
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: [["list"], ["json", { outputFile: "playwright-report.json" }]],
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || "http://localhost:3000",
    channel: "chrome",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "Desktop-1920x1080",
      use: {
        viewport: { width: 1920, height: 1080 },
        browserName: "chromium",
      },
    },
    {
      name: "Laptop-1366x768",
      use: {
        viewport: { width: 1366, height: 768 },
        browserName: "chromium",
      },
    },
    {
      name: "Tablet-768x1024",
      use: {
        viewport: { width: 768, height: 1024 },
        browserName: "chromium",
      },
    },
    {
      name: "Mobile-375x812",
      use: {
        viewport: { width: 375, height: 812 },
        browserName: "chromium",
        isMobile: true,
      },
    },
  ],
});
