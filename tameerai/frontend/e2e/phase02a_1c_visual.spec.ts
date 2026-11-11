import { test, expect } from "@playwright/test";
import * as path from "path";
import * as fs from "fs";

const ARTIFACT_SCREENSHOT_DIR = "C:\\Users\\muham\\.gemini\\antigravity\\brain\\85c7d051-a1b8-4814-8e24-56414fa9526c\\screenshots";

test.beforeAll(async () => {
  if (!fs.existsSync(ARTIFACT_SCREENSHOT_DIR)) {
    fs.mkdirSync(ARTIFACT_SCREENSHOT_DIR, { recursive: true });
  }
});

test.describe("Phase 02A.1C: Final Logo Visual Refinement & Independent Acceptance", () => {
  test("Desktop 1920x1080: Collapsed Emblem, Proportional Mascot Sizing, Welcome Screen & Avatars", async ({ page }, testInfo) => {
    const isMobileOrTablet = testInfo.project.name.includes("Mobile") || testInfo.project.name.includes("Tablet");
    if (isMobileOrTablet) return;

    console.log(`[Phase02A.1C] Running Desktop verification on ${testInfo.project.name}`);

    // Track network requests for performance audit (Task 5)
    const mascotRequests: { url: string; fromCache: boolean; status: number }[] = [];
    page.on("response", async (response) => {
      if (response.url().includes("orange_robot_mascot.svg")) {
        mascotRequests.push({
          url: response.url(),
          fromCache: response.fromServiceWorker() || response.status() === 304,
          status: response.status(),
        });
      }
    });

    // Step 1: Login
    await page.goto("/login");
    await page.waitForLoadState("domcontentloaded");
    await page.locator("input[type='email']").fill("e2e_tester@tameerai.pk");
    await page.locator("input[type='password']").fill("Password123!");
    await page.locator("button[type='submit']").click();

    await page.waitForURL("**/dashboard**", { timeout: 15000 });
    await page.waitForLoadState("networkidle");

    // =========================================================================
    // 1. Desktop Expanded Sidebar
    // =========================================================================
    const expandedLogo = page.locator("aside:visible img[alt='TameerAI Construction Assistant']").first();
    await expect(expandedLogo).toBeVisible();
    await expandedLogo.waitFor({ state: "visible" });
    await page.waitForTimeout(500);

    const expandedBox = await expandedLogo.boundingBox();
    expect(expandedBox).not.toBeNull();
    if (expandedBox) {
      console.log(`[Phase02A.1C] Expanded Logo BoundingBox: width=${expandedBox.width}px, height=${expandedBox.height}px`);
      expect(expandedBox.height).toBeGreaterThanOrEqual(38);
      expect(expandedBox.height).toBeLessThanOrEqual(46);
      expect(expandedBox.width).toBeGreaterThanOrEqual(120);
      expect(expandedBox.width).toBeLessThanOrEqual(140);
    }

    const expandedScreenshotPath = path.join(ARTIFACT_SCREENSHOT_DIR, "Phase02A_1C-Desktop-Expanded-Sidebar.png");
    await page.screenshot({ path: expandedScreenshotPath, fullPage: false });
    console.log(`[Phase02A.1C] Saved screenshot: ${expandedScreenshotPath}`);

    // =========================================================================
    // 2. Desktop Collapsed Sidebar Emblem Presentation (Task 1)
    // =========================================================================
    const collapseBtn = page.locator("button[aria-label='Collapse Sidebar']").first();
    await collapseBtn.click();
    await page.waitForTimeout(600);

    const collapsedContainer = page.locator("aside:visible div.overflow-hidden").first();
    await expect(collapsedContainer).toBeVisible();

    const collapsedContainerBox = await collapsedContainer.boundingBox();
    expect(collapsedContainerBox).not.toBeNull();
    if (collapsedContainerBox) {
      console.log(`[Phase02A.1C] Collapsed Emblem Container Box: width=${collapsedContainerBox.width}px, height=${collapsedContainerBox.height}px`);
      // Target compact presentation: approx 36-44px
      expect(collapsedContainerBox.width).toBeGreaterThanOrEqual(36);
      expect(collapsedContainerBox.width).toBeLessThanOrEqual(44);
      expect(collapsedContainerBox.height).toBeGreaterThanOrEqual(36);
      expect(collapsedContainerBox.height).toBeLessThanOrEqual(44);
    }

    const collapsedImg = collapsedContainer.locator("img[alt='TameerAI']").first();
    await expect(collapsedImg).toBeVisible();
    const collapsedImgSrc = await collapsedImg.getAttribute("src");
    expect(collapsedImgSrc).toContain("tameer_ai_orange.svg");

    const collapsedScreenshotPath = path.join(ARTIFACT_SCREENSHOT_DIR, "Phase02A_1C-Desktop-Collapsed-Sidebar.png");
    await page.screenshot({ path: collapsedScreenshotPath, fullPage: false });
    console.log(`[Phase02A.1C] Saved screenshot: ${collapsedScreenshotPath}`);

    // Expand sidebar back
    const expandBtn = page.locator("button[aria-label='Expand Sidebar']").first();
    await expandBtn.click();
    await page.waitForTimeout(600);

    // =========================================================================
    // 3. Navigate to AI Assistant & Verify Desktop Chat Header (Task 2)
    // =========================================================================
    await page.goto("/dashboard/ai-assistant");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(600);

    const chatHeaderLogo = page.locator("div.h-12 img[alt='TameerAI Assistant']").first();
    await expect(chatHeaderLogo).toBeVisible();
    const chatHeaderLogoSrc = await chatHeaderLogo.getAttribute("src");
    expect(chatHeaderLogoSrc).toContain("orange_robot_mascot.svg");

    const chatHeaderBox = await chatHeaderLogo.boundingBox();
    expect(chatHeaderBox).not.toBeNull();
    if (chatHeaderBox) {
      console.log(`[Phase02A.1C] Chat Header Mascot BoundingBox: width=${chatHeaderBox.width}px, height=${chatHeaderBox.height}px`);
      // Proportional 3:2 target: approx 42 x 28px
      expect(chatHeaderBox.width).toBeGreaterThanOrEqual(40);
      expect(chatHeaderBox.width).toBeLessThanOrEqual(44);
      expect(chatHeaderBox.height).toBeGreaterThanOrEqual(26);
      expect(chatHeaderBox.height).toBeLessThanOrEqual(30);
    }

    const chatHeaderScreenshotPath = path.join(ARTIFACT_SCREENSHOT_DIR, "Phase02A_1C-Desktop-Chat-Header.png");
    // Capture focused header area
    const headerBar = page.locator("div.h-12").first();
    await headerBar.screenshot({ path: chatHeaderScreenshotPath });
    console.log(`[Phase02A.1C] Saved screenshot: ${chatHeaderScreenshotPath}`);

    // =========================================================================
    // 4. Assistant Response Avatar (Task 2)
    // =========================================================================
    if ((await page.locator("div.overflow-y-auto img[alt='TameerAI']").count()) === 0) {
      const input = page.locator("input[placeholder*='Ask about']").first();
      await input.fill("Testing assistant avatar");
      const sendBtn = page.locator("button:has(svg.lucide-send)").first();
      await sendBtn.click();
      await page.waitForTimeout(600);
    }
    const assistantAvatar = page.locator("div.overflow-y-auto img[alt='TameerAI']").first();
    await expect(assistantAvatar).toBeVisible();
    const avatarSrc = await assistantAvatar.getAttribute("src");
    expect(avatarSrc).toContain("orange_robot_mascot.svg");

    const avatarBox = await assistantAvatar.boundingBox();
    expect(avatarBox).not.toBeNull();
    if (avatarBox) {
      console.log(`[Phase02A.1C] Assistant Avatar Mascot BoundingBox: width=${avatarBox.width}px, height=${avatarBox.height}px`);
      // Proportional 3:2 target: approx 40 x 27px
      expect(avatarBox.width).toBeGreaterThanOrEqual(38);
      expect(avatarBox.width).toBeLessThanOrEqual(42);
      expect(avatarBox.height).toBeGreaterThanOrEqual(25);
      expect(avatarBox.height).toBeLessThanOrEqual(29);
    }

    const avatarScreenshotPath = path.join(ARTIFACT_SCREENSHOT_DIR, "Phase02A_1C-Desktop-Assistant-Avatar.png");
    // Capture the initial message row
    const firstMessageRow = page.locator("div.overflow-y-auto > div").first();
    await firstMessageRow.screenshot({ path: avatarScreenshotPath });
    console.log(`[Phase02A.1C] Saved screenshot: ${avatarScreenshotPath}`);

    // =========================================================================
    // 5. Welcome Screen on New Chat (Task 2 & 3)
    // =========================================================================
    const newChatBtn = page.getByRole("button", { name: /New Chat|نئی چیٹ/i }).first();
    await newChatBtn.click();
    await page.waitForURL("**/dashboard/ai-assistant**", { timeout: 15000 });
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(800);

    const welcomeImg = page.locator("div.overflow-y-auto img[alt='TameerAI Assistant']").first();
    await expect(welcomeImg).toBeVisible();
    const welcomeImgSrc = await welcomeImg.getAttribute("src");
    expect(welcomeImgSrc).toContain("orange_robot_mascot.svg");

    const welcomeBox = await welcomeImg.boundingBox();
    expect(welcomeBox).not.toBeNull();
    if (welcomeBox) {
      console.log(`[Phase02A.1C] Welcome Mascot BoundingBox: width=${welcomeBox.width}px, height=${welcomeBox.height}px`);
      // Proportional 3:2 target: approx 72 x 48px
      expect(welcomeBox.width).toBeGreaterThanOrEqual(70);
      expect(welcomeBox.width).toBeLessThanOrEqual(75);
      expect(welcomeBox.height).toBeGreaterThanOrEqual(46);
      expect(welcomeBox.height).toBeLessThanOrEqual(50);
    }

    const welcomeScreenshotPath = path.join(ARTIFACT_SCREENSHOT_DIR, "Phase02A_1C-Desktop-Welcome-Screen.png");
    await page.screenshot({ path: welcomeScreenshotPath, fullPage: false });
    console.log(`[Phase02A.1C] Saved screenshot: ${welcomeScreenshotPath}`);

    // Performance logging
    console.log(`[Phase02A.1C] Total network requests for orange_robot_mascot.svg: ${mascotRequests.length}`);
  });

  test("Mobile 375x812: Drawer Brand Logo & Mobile Chat Mascot (Task 3)", async ({ page }, testInfo) => {
    const isMobile = testInfo.project.name.includes("Mobile-375x812");
    if (!isMobile) return;

    console.log(`[Phase02A.1C] Running Mobile verification on ${testInfo.project.name}`);

    // Step 1: Login
    await page.goto("/login");
    await page.waitForLoadState("domcontentloaded");
    await page.locator("input[type='email']").fill("e2e_tester@tameerai.pk");
    await page.locator("input[type='password']").fill("Password123!");
    await page.locator("button[type='submit']").click();

    await page.waitForURL("**/dashboard**", { timeout: 15000 });
    await page.waitForLoadState("networkidle");

    // =========================================================================
    // 6. Mobile Navigation Drawer (Task 3)
    // =========================================================================
    const mobileMenuBtn = page.locator("button[aria-label='Toggle navigation']").first();
    await mobileMenuBtn.click();
    await page.waitForTimeout(600);

    const drawerLogo = page.locator("aside:visible img[alt='TameerAI Construction Assistant']").first();
    await expect(drawerLogo).toBeVisible();
    const drawerLogoSrc = await drawerLogo.getAttribute("src");
    expect(drawerLogoSrc).toContain("tameer_ai_orange.svg");

    const drawerLogoBox = await drawerLogo.boundingBox();
    expect(drawerLogoBox).not.toBeNull();
    if (drawerLogoBox) {
      console.log(`[Phase02A.1C] Mobile Drawer Logo BoundingBox: width=${drawerLogoBox.width}px, height=${drawerLogoBox.height}px`);
      expect(drawerLogoBox.height).toBeGreaterThanOrEqual(36);
      expect(drawerLogoBox.height).toBeLessThanOrEqual(44);
      expect(drawerLogoBox.width).toBeGreaterThanOrEqual(110);
      expect(drawerLogoBox.width).toBeLessThanOrEqual(130);
    }

    const drawerScreenshotPath = path.join(ARTIFACT_SCREENSHOT_DIR, "Phase02A_1C-Mobile-Drawer.png");
    await page.screenshot({ path: drawerScreenshotPath, fullPage: false });
    console.log(`[Phase02A.1C] Saved screenshot: ${drawerScreenshotPath}`);

    // =========================================================================
    // 7. Mobile Chat Interface (Task 3)
    // =========================================================================
    const mobileNewChatBtn = page.locator("aside:visible").getByRole("button", { name: /New Chat|نئی چیٹ/i }).first();
    await mobileNewChatBtn.click();
    await page.waitForURL("**/dashboard/ai-assistant**", { timeout: 10000 });
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(600);

    // Send a message so both welcome/empty or stream avatar are verified
    const chatInput = page.locator("input[placeholder*='Ask about']").first();
    await chatInput.fill("What is the minimum staircase width per PBC 2021?");
    await chatInput.press("Enter");

    const mobileAvatar = page.locator("div.overflow-y-auto img[alt='TameerAI']").first();
    await expect(mobileAvatar).toBeVisible({ timeout: 10000 });
    const mobileAvatarSrc = await mobileAvatar.getAttribute("src");
    expect(mobileAvatarSrc).toContain("orange_robot_mascot.svg");

    const mobileChatScreenshotPath = path.join(ARTIFACT_SCREENSHOT_DIR, "Phase02A_1C-Mobile-Chat.png");
    await page.screenshot({ path: mobileChatScreenshotPath, fullPage: false });
    console.log(`[Phase02A.1C] Saved screenshot: ${mobileChatScreenshotPath}`);
  });
});

