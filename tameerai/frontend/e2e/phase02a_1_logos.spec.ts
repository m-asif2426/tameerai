import { test, expect } from "@playwright/test";
import * as path from "path";
import * as fs from "fs";

const ARTIFACT_SCREENSHOT_DIR = "C:\\Users\\muham\\.gemini\\antigravity\\brain\\85c7d051-a1b8-4814-8e24-56414fa9526c\\screenshots";

test.beforeAll(async () => {
  if (!fs.existsSync(ARTIFACT_SCREENSHOT_DIR)) {
    fs.mkdirSync(ARTIFACT_SCREENSHOT_DIR, { recursive: true });
  }
});

test.describe("Phase 02A.1A: Final Brand Visual Acceptance & New Chat Verification", () => {
  test("Desktop 1920x1080 & Laptop 1366x768: Sidebar Sizing, New Chat CTA & Chat Avatars", async ({ page }, testInfo) => {
    const isMobileOrTablet = testInfo.project.name.includes("Mobile") || testInfo.project.name.includes("Tablet");
    if (isMobileOrTablet) return;

    console.log(`[Phase02A.1A] Running Desktop/Laptop verification on ${testInfo.project.name}`);

    // Step 1: Login
    await page.goto("/login");
    await page.waitForLoadState("domcontentloaded");
    await page.locator("input[type='email']").fill("e2e_tester@tameerai.pk");
    await page.locator("input[type='password']").fill("Password123!");
    await page.locator("button[type='submit']").click();

    await page.waitForURL("**/dashboard**", { timeout: 15000 });
    await page.waitForLoadState("networkidle");

    // 1. Verify Expanded Sidebar Header Brand Logo & Legibility
    const expandedLogo = page.locator("aside:visible img[alt='TameerAI Construction Assistant']").first();
    await expect(expandedLogo).toBeVisible();
    await expandedLogo.waitFor({ state: "visible" });
    await page.waitForTimeout(500);
    const expandedLogoSrc = await expandedLogo.getAttribute("src");
    expect(expandedLogoSrc).toContain("tameer_ai_orange.svg");

    const expandedBox = await expandedLogo.boundingBox();
    expect(expandedBox).not.toBeNull();
    if (expandedBox) {
      console.log(`[Phase02A.1A] Expanded Logo BoundingBox: width=${expandedBox.width}px, height=${expandedBox.height}px`);
      // Verified proportional legibility sizing:
      expect(expandedBox.height).toBeGreaterThanOrEqual(38);
      expect(expandedBox.height).toBeLessThanOrEqual(46);
      expect(expandedBox.width).toBeGreaterThanOrEqual(100);
      expect(expandedBox.width).toBeLessThanOrEqual(140);
    }

    // 2. Verify New Chat CTA Label
    const newChatBtn = page.getByRole("button", { name: /New Chat|نئی چیٹ/i }).first();
    await expect(newChatBtn).toBeVisible();

    // Capture Expanded Sidebar Screenshot
    const expandedScreenshot = path.join(ARTIFACT_SCREENSHOT_DIR, `Phase02A_1A-${testInfo.project.name}-Expanded-Sidebar.png`);
    await page.screenshot({ path: expandedScreenshot, fullPage: false });
    console.log(`[Phase02A.1A] Saved screenshot: ${expandedScreenshot}`);

    // 3. Test Sidebar Collapse and Verify Collapsed Brand Mark
    const collapseBtn = page.locator("button[aria-label='Collapse Sidebar']").first();
    await collapseBtn.click();
    await page.waitForTimeout(600);

    const collapsedLogo = page.locator("aside:visible img[alt='TameerAI']").first();
    await expect(collapsedLogo).toBeVisible();
    const collapsedLogoSrc = await collapsedLogo.getAttribute("src");
    expect(collapsedLogoSrc).toContain("tameer_ai_orange.svg");

    const collapsedBox = await collapsedLogo.boundingBox();
    expect(collapsedBox).not.toBeNull();
    if (collapsedBox) {
      console.log(`[Phase02A.1A] Collapsed Logo BoundingBox: width=${collapsedBox.width}px, height=${collapsedBox.height}px`);
      expect(collapsedBox.width).toBeGreaterThanOrEqual(36);
      expect(collapsedBox.width).toBeLessThanOrEqual(48);
    }

    // Capture Collapsed Sidebar Screenshot
    const collapsedScreenshot = path.join(ARTIFACT_SCREENSHOT_DIR, `Phase02A_1A-${testInfo.project.name}-Collapsed-Sidebar.png`);
    await page.screenshot({ path: collapsedScreenshot, fullPage: false });
    console.log(`[Phase02A.1A] Saved screenshot: ${collapsedScreenshot}`);

    // Expand sidebar back
    const expandBtn = page.locator("button[aria-label='Expand Sidebar']").first();
    await expandBtn.click();
    await page.waitForTimeout(600);

    // 4. Test New Chat CTA Click Functionality
    console.log("[Phase02A.1A] Clicking New Chat CTA to verify session creation...");
    await newChatBtn.click();
    await page.waitForURL("**/dashboard/ai-assistant**", { timeout: 10000 });
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(500);

    // 5. Verify Main Chat Header Icon
    const chatHeaderLogo = page.locator("div.h-12 img[alt='TameerAI Assistant']").first();
    await expect(chatHeaderLogo).toBeVisible();
    const chatHeaderLogoSrc = await chatHeaderLogo.getAttribute("src");
    expect(chatHeaderLogoSrc).toContain("orange_robot_mascot.svg");

    const chatHeaderBox = await chatHeaderLogo.boundingBox();
    expect(chatHeaderBox).not.toBeNull();
    if (chatHeaderBox) {
      console.log(`[Phase02A.1A] Chat Header Logo BoundingBox: width=${chatHeaderBox.width}px, height=${chatHeaderBox.height}px`);
      expect(chatHeaderBox.height).toBeGreaterThanOrEqual(28);
      expect(chatHeaderBox.height).toBeLessThanOrEqual(36);
      expect(chatHeaderBox.width).toBeGreaterThanOrEqual(28);
      expect(chatHeaderBox.width).toBeLessThanOrEqual(36);
    }

    // 6. Verify Assistant Message Avatar in Stream
    const assistantAvatar = page.locator("div.overflow-y-auto img[alt='TameerAI']").first();
    await expect(assistantAvatar).toBeVisible();
    const avatarSrc = await assistantAvatar.getAttribute("src");
    expect(avatarSrc).toContain("orange_robot_mascot.svg");

    const avatarBox = await assistantAvatar.boundingBox();
    expect(avatarBox).not.toBeNull();
    if (avatarBox) {
      console.log(`[Phase02A.1A] Assistant Avatar BoundingBox: width=${avatarBox.width}px, height=${avatarBox.height}px`);
      expect(avatarBox.height).toBeGreaterThanOrEqual(26);
      expect(avatarBox.height).toBeLessThanOrEqual(34);
      expect(avatarBox.width).toBeGreaterThanOrEqual(26);
      expect(avatarBox.width).toBeLessThanOrEqual(34);
    }

    // Capture Chat Interface Screenshot
    const chatScreenshot = path.join(ARTIFACT_SCREENSHOT_DIR, `Phase02A_1A-${testInfo.project.name}-Chat-Avatars.png`);
    await page.screenshot({ path: chatScreenshot, fullPage: false });
    console.log(`[Phase02A.1A] Saved screenshot: ${chatScreenshot}`);
  });

  test("Mobile & Tablet Viewports: Drawer Brand Logo & Mobile Chat", async ({ page }, testInfo) => {
    const isMobileOrTablet = testInfo.project.name.includes("Mobile") || testInfo.project.name.includes("Tablet");
    if (!isMobileOrTablet) return;

    console.log(`[Phase02A.1A] Running Mobile/Tablet verification on ${testInfo.project.name}`);

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

    // Verify Drawer contains Expanded Brand Logo
    const drawerLogo = page.locator("aside:visible img[alt='TameerAI Construction Assistant']").first();
    await expect(drawerLogo).toBeVisible();
    const drawerLogoSrc = await drawerLogo.getAttribute("src");
    expect(drawerLogoSrc).toContain("tameer_ai_orange.svg");

    const drawerLogoBox = await drawerLogo.boundingBox();
    expect(drawerLogoBox).not.toBeNull();
    if (drawerLogoBox) {
      console.log(`[Phase02A.1A] Mobile Drawer Logo BoundingBox: width=${drawerLogoBox.width}px, height=${drawerLogoBox.height}px`);
      expect(drawerLogoBox.height).toBeGreaterThanOrEqual(36);
      expect(drawerLogoBox.height).toBeLessThanOrEqual(46);
      expect(drawerLogoBox.width).toBeLessThanOrEqual(140);
    }

    // Verify New Chat CTA in Drawer
    const mobileNewChatBtn = page.locator("aside:visible").getByRole("button", { name: /New Chat|نئی چیٹ/i }).first();
    await expect(mobileNewChatBtn).toBeVisible();

    // Capture Mobile Drawer Screenshot
    const drawerScreenshot = path.join(ARTIFACT_SCREENSHOT_DIR, `Phase02A_1A-${testInfo.project.name}-Drawer.png`);
    await page.screenshot({ path: drawerScreenshot, fullPage: false });
    console.log(`[Phase02A.1A] Saved screenshot: ${drawerScreenshot}`);

    // Click New Chat in Drawer to verify navigation
    await mobileNewChatBtn.click();
    await page.waitForURL("**/dashboard/ai-assistant**", { timeout: 10000 });
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(500);

    // Verify Mobile Chat Header Icon
    const chatHeaderLogo = page.locator("div.h-12 img[alt='TameerAI Assistant']").first();
    await expect(chatHeaderLogo).toBeVisible();

    // Verify Assistant Message Avatar in Stream
    const assistantAvatar = page.locator("div.overflow-y-auto img[alt='TameerAI']").first();
    await expect(assistantAvatar).toBeVisible();

    // Capture Mobile Chat View Screenshot
    const mobileChatScreenshot = path.join(ARTIFACT_SCREENSHOT_DIR, `Phase02A_1A-${testInfo.project.name}-Chat.png`);
    await page.screenshot({ path: mobileChatScreenshot, fullPage: false });
    console.log(`[Phase02A.1A] Saved screenshot: ${mobileChatScreenshot}`);
  });
});
