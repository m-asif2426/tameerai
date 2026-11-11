import { test, expect } from "@playwright/test";
import * as path from "path";
import * as fs from "fs";

const ARTIFACT_SCREENSHOT_DIR = "C:\\Users\\muham\\.gemini\\antigravity\\brain\\85c7d051-a1b8-4814-8e24-56414fa9526c\\screenshots";

test.beforeAll(async () => {
  if (!fs.existsSync(ARTIFACT_SCREENSHOT_DIR)) {
    fs.mkdirSync(ARTIFACT_SCREENSHOT_DIR, { recursive: true });
  }
});

test.describe("Phase 02A: Combined Sidebar & Navigation Refactor E2E Verification", () => {
  test("Desktop Combined Sidebar, Consultation Management & Mobile Drawer", async ({ page }, testInfo) => {
    const isMobile = testInfo.project.name.includes("Mobile") || testInfo.project.name.includes("Tablet");

    console.log(`[Phase02A] Testing on ${testInfo.project.name}`);

    // Step 1: Login
    await page.goto("/login");
    await page.waitForLoadState("domcontentloaded");

    const emailInput = page.locator("input[type='email']");
    const passwordInput = page.locator("input[type='password']");
    await emailInput.fill("e2e_tester@tameerai.pk");
    await passwordInput.fill("Password123!");
    await page.locator("button[type='submit']").click();

    await page.waitForURL("**/dashboard**", { timeout: 15000 });
    await page.waitForLoadState("networkidle");

    if (!isMobile) {
      // -----------------------------------------------------------------------
      // DESKTOP COMBINED SIDEBAR VERIFICATION
      // -----------------------------------------------------------------------
      console.log("[Phase02A] Verifying Desktop Combined Sidebar...");

      // 1. Verify Brand Header
      await expect(page.locator("aside img[alt*='TameerAI']").first()).toBeVisible();

      // 2. Verify + New Chat CTA
      const newConsultationBtn = page.getByRole("button", { name: /New Chat|New Consultation|نئی چیٹ|نیا مشورہ/i }).first();
      await expect(newConsultationBtn).toBeVisible();

      // 3. Verify Search Conversations Input
      const searchConversationsInput = page.locator("input[placeholder*='Filter conversations']");
      await expect(searchConversationsInput).toBeVisible();

      // 4. Verify Consultations Section Header
      const consultationsHeader = page.getByText("Recent Consultations").first();
      await expect(consultationsHeader).toBeVisible();

      // 5. Verify Engineering Modules Header & 9 Navigation Items
      const engineeringHeader = page.getByText("Engineering Modules").first();
      await expect(engineeringHeader).toBeVisible();

      const expectedTools = [
        "Dashboard",
        "Projects",
        "Cost Intelligence",
        "Structural Safety",
        "Regulations",
        "Compliance Check",
        "Contract Analyzer",
        "Audit & Inspection",
        "Reports",
      ];
      for (const tool of expectedTools) {
        await expect(page.locator(`nav a:has-text('${tool}')`).first()).toBeVisible();
      }

      // Verify Structural Safety rule count badge
      const safetyBadge = page.locator("nav a:has-text('Structural Safety') span:has-text('38 Rules')");
      await expect(safetyBadge).toBeVisible();

      // 6. Verify Authenticated User Profile Footer
      const logoutBtn = page.locator("aside button[title*='Logout'], aside button[aria-label='Logout']").first();
      await expect(logoutBtn).toBeVisible();

      // Take Initial Desktop Dashboard Screenshot
      const desktopDashboardPath = path.join(ARTIFACT_SCREENSHOT_DIR, "Phase02A-Desktop-Combined-Sidebar-Dashboard.png");
      await page.screenshot({ path: desktopDashboardPath, fullPage: false });
      console.log(`[Phase02A] Desktop dashboard screenshot saved to: ${desktopDashboardPath}`);

      // 7. Test Clicking + New Consultation
      console.log("[Phase02A] Testing + New Consultation click...");
      await newConsultationBtn.click();
      await page.waitForURL("**/dashboard/ai-assistant**", { timeout: 10000 });
      await page.waitForTimeout(1000);

      // Take Desktop AI Assistant Screenshot with Combined Sidebar
      const desktopChatPath = path.join(ARTIFACT_SCREENSHOT_DIR, "Phase02A-Desktop-Combined-Sidebar-AIAssistant.png");
      await page.screenshot({ path: desktopChatPath, fullPage: false });
      console.log(`[Phase02A] Desktop AI Assistant screenshot saved to: ${desktopChatPath}`);

    } else {
      // -----------------------------------------------------------------------
      // MOBILE SLIDE-OVER DRAWER VERIFICATION
      // -----------------------------------------------------------------------
      console.log("[Phase02A] Verifying Mobile Drawer on Viewport...");

      // 1. Open mobile menu via hamburger button
      const hamburgerBtn = page.locator("header button[aria-label='Toggle navigation']");
      await expect(hamburgerBtn).toBeVisible();
      await hamburgerBtn.click();
      await page.waitForTimeout(600);

      // 2. Verify drawer overlay is open
      const drawer = page.locator("aside").last();
      await expect(drawer).toBeVisible();

      // 3. Verify + New Chat CTA inside mobile drawer
      const mobileNewBtn = drawer.getByRole("button", { name: /New Chat|New Consultation|نئی چیٹ|نیا مشورہ/i }).first();
      await expect(mobileNewBtn).toBeVisible();

      // 4. Verify Engineering Modules in mobile drawer
      await expect(drawer.getByText("Engineering Modules").first()).toBeVisible();

      // 5. Verify Close Button
      const closeBtn = page.locator("button[aria-label='Close menu']");
      await expect(closeBtn).toBeVisible();

      // Take Mobile Drawer Screenshot
      const mobileScreenshotPath = path.join(ARTIFACT_SCREENSHOT_DIR, "Phase02A-Mobile-Combined-Drawer.png");
      await page.screenshot({ path: mobileScreenshotPath, fullPage: false });
      console.log(`[Phase02A] Mobile screenshot saved to: ${mobileScreenshotPath}`);

      // Close drawer
      await closeBtn.click();
      await page.waitForTimeout(400);

      // Take Mobile Closed State Screenshot
      const mobileClosedPath = path.join(ARTIFACT_SCREENSHOT_DIR, "Phase02A-Mobile-Closed-State.png");
      await page.screenshot({ path: mobileClosedPath, fullPage: false });
      console.log(`[Phase02A] Mobile closed screenshot saved to: ${mobileClosedPath}`);
    }
  });
});
