import { test, expect } from "@playwright/test";
import * as path from "path";
import * as fs from "fs";

const ARTIFACT_SCREENSHOT_DIR = "C:\\Users\\muham\\.gemini\\antigravity\\brain\\85c7d051-a1b8-4814-8e24-56414fa9526c\\screenshots";

test.beforeAll(async () => {
  if (!fs.existsSync(ARTIFACT_SCREENSHOT_DIR)) {
    fs.mkdirSync(ARTIFACT_SCREENSHOT_DIR, { recursive: true });
  }
});

test.describe("Phase 02A.1B: Final Official Brand Asset Replacement Verification", () => {
  test("Desktop 1920x1080 & Laptop 1366x768: Official Brand Logos & Mascot Avatars", async ({ page }, testInfo) => {
    const isMobileOrTablet = testInfo.project.name.includes("Mobile") || testInfo.project.name.includes("Tablet");
    if (isMobileOrTablet) return;

    console.log(`[Phase02A.1B] Running Desktop/Laptop verification on ${testInfo.project.name}`);

    // Step 1: Login
    await page.goto("/login");
    await page.waitForLoadState("domcontentloaded");
    await page.locator("input[type='email']").fill("e2e_tester@tameerai.pk");
    await page.locator("input[type='password']").fill("Password123!");
    await page.locator("button[type='submit']").click();

    await page.waitForURL("**/dashboard**", { timeout: 15000 });
    await page.waitForLoadState("networkidle");

    // 1. Verify Expanded Sidebar Header: tameer_ai_orange.svg
    const expandedLogo = page.locator("aside:visible img[alt='TameerAI Construction Assistant']").first();
    await expect(expandedLogo).toBeVisible();
    await expandedLogo.waitFor({ state: "visible" });
    await page.waitForTimeout(500);
    const expandedLogoSrc = await expandedLogo.getAttribute("src");
    expect(expandedLogoSrc).toContain("tameer_ai_orange.svg");

    const expandedBox = await expandedLogo.boundingBox();
    expect(expandedBox).not.toBeNull();
    if (expandedBox) {
      console.log(`[Phase02A.1B] Expanded Logo BoundingBox: width=${expandedBox.width}px, height=${expandedBox.height}px`);
      expect(expandedBox.height).toBeGreaterThanOrEqual(36);
      expect(expandedBox.height).toBeLessThanOrEqual(46);
      expect(expandedBox.width).toBeGreaterThanOrEqual(100);
      expect(expandedBox.width).toBeLessThanOrEqual(140);
    }

    // 2. Verify New Chat CTA Label
    const newChatBtn = page.getByRole("button", { name: /New Chat|نئی چیٹ/i }).first();
    await expect(newChatBtn).toBeVisible();

    // Capture Expanded Sidebar Screenshot
    const expandedScreenshot = path.join(ARTIFACT_SCREENSHOT_DIR, `Phase02A_1B-${testInfo.project.name}-Expanded-Sidebar.png`);
    await page.screenshot({ path: expandedScreenshot, fullPage: false });
    console.log(`[Phase02A.1B] Saved screenshot: ${expandedScreenshot}`);

    // 3. Test Sidebar Collapse and Verify Collapsed Brand Mark: tameer_ai_orange.svg
    const collapseBtn = page.locator("button[aria-label='Collapse Sidebar']").first();
    await collapseBtn.click();
    await page.waitForTimeout(600);

    const collapsedContainer = page.locator("aside:visible div.overflow-hidden").first();
    await expect(collapsedContainer).toBeVisible();

    const collapsedContainerBox = await collapsedContainer.boundingBox();
    expect(collapsedContainerBox).not.toBeNull();
    if (collapsedContainerBox) {
      console.log(`[Phase02A.1B] Collapsed Emblem Container Box: width=${collapsedContainerBox.width}px, height=${collapsedContainerBox.height}px`);
      expect(collapsedContainerBox.width).toBeGreaterThanOrEqual(36);
      expect(collapsedContainerBox.width).toBeLessThanOrEqual(44);
      expect(collapsedContainerBox.height).toBeGreaterThanOrEqual(36);
      expect(collapsedContainerBox.height).toBeLessThanOrEqual(44);
    }

    // Capture Collapsed Sidebar Screenshot
    const collapsedScreenshot = path.join(ARTIFACT_SCREENSHOT_DIR, `Phase02A_1B-${testInfo.project.name}-Collapsed-Sidebar.png`);
    await page.screenshot({ path: collapsedScreenshot, fullPage: false });
    console.log(`[Phase02A.1B] Saved screenshot: ${collapsedScreenshot}`);

    // Expand sidebar back
    const expandBtn = page.locator("button[aria-label='Expand Sidebar']").first();
    await expandBtn.click();
    await page.waitForTimeout(600);

    // 4. Test New Chat CTA Click Functionality
    console.log("[Phase02A.1B] Clicking New Chat CTA to verify session creation...");
    await newChatBtn.click();
    await page.waitForURL("**/dashboard/ai-assistant**", { timeout: 10000 });
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(500);

    // 5. Verify Main Chat Header Icon: orange_robot_mascot.svg
    const chatHeaderLogo = page.locator("div.h-12 img[alt='TameerAI Assistant']").first();
    await expect(chatHeaderLogo).toBeVisible();
    const chatHeaderLogoSrc = await chatHeaderLogo.getAttribute("src");
    expect(chatHeaderLogoSrc).toContain("orange_robot_mascot.svg");

    const chatHeaderBox = await chatHeaderLogo.boundingBox();
    expect(chatHeaderBox).not.toBeNull();
    if (chatHeaderBox) {
      console.log(`[Phase02A.1B] Chat Header Mascot BoundingBox: width=${chatHeaderBox.width}px, height=${chatHeaderBox.height}px`);
      expect(chatHeaderBox.height).toBeGreaterThanOrEqual(26);
      expect(chatHeaderBox.height).toBeLessThanOrEqual(30);
      expect(chatHeaderBox.width).toBeGreaterThanOrEqual(40);
      expect(chatHeaderBox.width).toBeLessThanOrEqual(44);
    }

    // 6. Verify Assistant Message Avatar in Stream: orange_robot_mascot.svg
    // Click suggested prompt or type to ensure avatar is visible
    const quickPrompt = page.locator("div.overflow-x-auto button").first();
    if (await quickPrompt.isVisible()) {
      await quickPrompt.click();
      await page.waitForTimeout(600);
    }

    const assistantAvatar = page.locator("div.overflow-y-auto img[alt='TameerAI']").first();
    await expect(assistantAvatar).toBeVisible();
    const avatarSrc = await assistantAvatar.getAttribute("src");
    expect(avatarSrc).toContain("orange_robot_mascot.svg");

    const avatarBox = await assistantAvatar.boundingBox();
    expect(avatarBox).not.toBeNull();
    if (avatarBox) {
      console.log(`[Phase02A.1B] Assistant Avatar Mascot BoundingBox: width=${avatarBox.width}px, height=${avatarBox.height}px`);
      expect(avatarBox.height).toBeGreaterThanOrEqual(25);
      expect(avatarBox.height).toBeLessThanOrEqual(29);
      expect(avatarBox.width).toBeGreaterThanOrEqual(38);
      expect(avatarBox.width).toBeLessThanOrEqual(42);
    }

    // Capture Chat Interface Screenshot
    const chatScreenshot = path.join(ARTIFACT_SCREENSHOT_DIR, `Phase02A_1B-${testInfo.project.name}-Chat-Avatars.png`);
    await page.screenshot({ path: chatScreenshot, fullPage: false });
    console.log(`[Phase02A.1B] Saved screenshot: ${chatScreenshot}`);
  });

  test("Mobile & Tablet Viewports: Drawer Brand Logo & Mobile Chat Mascot", async ({ page }, testInfo) => {
    const isMobileOrTablet = testInfo.project.name.includes("Mobile") || testInfo.project.name.includes("Tablet");
    if (!isMobileOrTablet) return;

    console.log(`[Phase02A.1B] Running Mobile/Tablet verification on ${testInfo.project.name}`);

    // Step 1: Login
    await page.goto("/login");
    await page.waitForLoadState("domcontentloaded");
    await page.locator("input[type='email']").fill("e2e_tester@tameerai.pk");
    await page.locator("input[type='password']").fill("Password123!");
    await page.locator("button[type='submit']").click();

    await page.waitForURL("**/dashboard**", { timeout: 15000 });
    await page.waitForLoadState("networkidle");

    // Open Mobile Drawer
    const mobileMenuBtn = page.locator("button[aria-label='Toggle navigation']").first();
    await mobileMenuBtn.click();
    await page.waitForTimeout(600);

    // Verify Drawer contains Expanded Brand Logo: tameer_ai_orange.svg
    const drawerLogo = page.locator("aside:visible img[alt='TameerAI Construction Assistant']").first();
    await expect(drawerLogo).toBeVisible();
    const drawerLogoSrc = await drawerLogo.getAttribute("src");
    expect(drawerLogoSrc).toContain("tameer_ai_orange.svg");

    const drawerLogoBox = await drawerLogo.boundingBox();
    expect(drawerLogoBox).not.toBeNull();
    if (drawerLogoBox) {
      console.log(`[Phase02A.1B] Mobile Drawer Logo BoundingBox: width=${drawerLogoBox.width}px, height=${drawerLogoBox.height}px`);
      expect(drawerLogoBox.height).toBeGreaterThanOrEqual(36);
      expect(drawerLogoBox.height).toBeLessThanOrEqual(46);
      expect(drawerLogoBox.width).toBeGreaterThanOrEqual(100);
      expect(drawerLogoBox.width).toBeLessThanOrEqual(140);
    }

    // Verify New Chat CTA in Drawer
    const mobileNewChatBtn = page.locator("aside:visible").getByRole("button", { name: /New Chat|نئی چیٹ/i }).first();
    await expect(mobileNewChatBtn).toBeVisible();

    // Capture Drawer Screenshot
    const drawerScreenshot = path.join(ARTIFACT_SCREENSHOT_DIR, `Phase02A_1B-${testInfo.project.name}-Drawer.png`);
    await page.screenshot({ path: drawerScreenshot, fullPage: false });
    console.log(`[Phase02A.1B] Saved screenshot: ${drawerScreenshot}`);

    // Click New Chat CTA in Drawer
    await mobileNewChatBtn.click();
    await page.waitForURL("**/dashboard/ai-assistant**", { timeout: 10000 });
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(500);

    // Verify Header Mascot Icon on Mobile/Tablet
    const chatHeaderLogo = page.locator("div.h-12 img[alt='TameerAI Assistant']").first();
    await expect(chatHeaderLogo).toBeVisible();
    const chatHeaderLogoSrc = await chatHeaderLogo.getAttribute("src");
    expect(chatHeaderLogoSrc).toContain("orange_robot_mascot.svg");

    // Verify Mascot Icon in Chat Area on Mobile/Tablet (Welcome or Avatar)
    const mobileMascot = page.locator("div.overflow-y-auto img[alt*='TameerAI']").first();
    await expect(mobileMascot).toBeVisible();
    const avatarSrc = await mobileMascot.getAttribute("src");
    expect(avatarSrc).toContain("orange_robot_mascot.svg");

    // Capture Mobile Chat Screenshot
    const chatMobileScreenshot = path.join(ARTIFACT_SCREENSHOT_DIR, `Phase02A_1B-${testInfo.project.name}-Chat.png`);
    await page.screenshot({ path: chatMobileScreenshot, fullPage: false });
    console.log(`[Phase02A.1B] Saved screenshot: ${chatMobileScreenshot}`);
  });
});

