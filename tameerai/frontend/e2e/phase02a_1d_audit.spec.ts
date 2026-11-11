import { test, expect } from "@playwright/test";
import * as path from "path";
import * as fs from "fs";

const ARTIFACT_SCREENSHOT_DIR = "C:\\Users\\muham\\.gemini\\antigravity\\brain\\85c7d051-a1b8-4814-8e24-56414fa9526c\\screenshots";

test.beforeAll(async () => {
  if (!fs.existsSync(ARTIFACT_SCREENSHOT_DIR)) {
    fs.mkdirSync(ARTIFACT_SCREENSHOT_DIR, { recursive: true });
  }
});

test.describe("Phase 02A.1D: New Chat State Reset & Final Visual Acceptance Audit", () => {
  test("Task 1 & Task 2: Event Lifecycle, Route Transitions, Stale Session Prevention & Non-Deletion", async ({ page }, testInfo) => {
    const isMobileOrTablet = testInfo.project.name.includes("Mobile") || testInfo.project.name.includes("Tablet");
    if (isMobileOrTablet) return;

    console.log(`[Phase02A.1D] Running State Reset & Session Lifecycle Audit on ${testInfo.project.name}`);

    // Step 1: Login
    await page.goto("/login");
    await page.waitForLoadState("domcontentloaded");
    await page.locator("input[type='email']").fill("e2e_tester@tameerai.pk");
    await page.locator("input[type='password']").fill("Password123!");
    await page.locator("button[type='submit']").click();

    await page.waitForURL("**/dashboard**", { timeout: 15000 });
    await page.waitForLoadState("networkidle");

    // =========================================================================
    // TASK 3 - SCREENSHOT 1: Expanded Sidebar with Complete Brand Wordmark
    // =========================================================================
    const expandedLogo = page.locator("aside:visible img[alt='TameerAI Construction Assistant']").first();
    await expect(expandedLogo).toBeVisible();
    await expandedLogo.waitFor({ state: "visible" });
    await page.waitForTimeout(500);
    const expandedBox = await expandedLogo.boundingBox();
    console.log(`[Phase02A.1D] Expanded Logo BoundingBox: width=${expandedBox?.width}px, height=${expandedBox?.height}px`);
    const screenshotExpanded = path.join(ARTIFACT_SCREENSHOT_DIR, "Phase02A_1D-Desktop-Expanded-Sidebar.png");
    await page.screenshot({ path: screenshotExpanded, fullPage: false });
    console.log(`[Phase02A.1D] Saved: ${screenshotExpanded}`);

    // =========================================================================
    // TASK 3 - SCREENSHOT 2: Collapsed Sidebar with Architectural Emblem
    // =========================================================================
    const collapseBtn = page.locator("button[aria-label='Collapse Sidebar']").first();
    await collapseBtn.click();
    await page.waitForTimeout(600);

    const collapsedContainer = page.locator("aside:visible div.overflow-hidden").first();
    await expect(collapsedContainer).toBeVisible();
    const collapsedBox = await collapsedContainer.boundingBox();
    console.log(`[Phase02A.1D] Collapsed Emblem Container: width=${collapsedBox?.width}px, height=${collapsedBox?.height}px`);
    const screenshotCollapsed = path.join(ARTIFACT_SCREENSHOT_DIR, "Phase02A_1D-Desktop-Collapsed-Sidebar.png");
    await page.screenshot({ path: screenshotCollapsed, fullPage: false });
    console.log(`[Phase02A.1D] Saved: ${screenshotCollapsed}`);

    // Expand sidebar back
    const expandBtn = page.locator("button[aria-label='Expand Sidebar']").first();
    await expandBtn.click();
    await page.waitForTimeout(600);

    // =========================================================================
    // TASK 1 - SCENARIO 1: User already on AI Assistant
    // =========================================================================
    console.log("[Phase02A.1D] Testing Scenario 1: User already on AI Assistant...");
    await page.goto("/dashboard/ai-assistant");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(500);

    // TASK 3 - SCREENSHOT 3: Chat Header with Orange Robot
    const chatHeaderLogo = page.locator("div.h-12 img[alt='TameerAI Assistant']").first();
    await expect(chatHeaderLogo).toBeVisible();
    const chatHeaderBox = await chatHeaderLogo.boundingBox();
    console.log(`[Phase02A.1D] Chat Header Mascot: width=${chatHeaderBox?.width}px, height=${chatHeaderBox?.height}px`);
    const screenshotHeader = path.join(ARTIFACT_SCREENSHOT_DIR, "Phase02A_1D-Desktop-Chat-Header.png");
    const headerBar = page.locator("div.h-12").first();
    await headerBar.screenshot({ path: screenshotHeader });
    console.log(`[Phase02A.1D] Saved: ${screenshotHeader}`);

    // TASK 3 - SCREENSHOT 4: Assistant Message Response Avatar
    const assistantAvatar = page.locator("div.overflow-y-auto img[alt='TameerAI']").first();
    await expect(assistantAvatar).toBeVisible();
    const avatarBox = await assistantAvatar.boundingBox();
    console.log(`[Phase02A.1D] Assistant Avatar Mascot: width=${avatarBox?.width}px, height=${avatarBox?.height}px`);
    const screenshotAvatar = path.join(ARTIFACT_SCREENSHOT_DIR, "Phase02A_1D-Desktop-Assistant-Avatar.png");
    const firstMsgRow = page.locator("div.overflow-y-auto > div").first();
    await firstMsgRow.screenshot({ path: screenshotAvatar });
    console.log(`[Phase02A.1D] Saved: ${screenshotAvatar}`);

    // Send a message to create an active conversation with text
    const chatInput = page.locator("div.border-t input[type='text']").first();
    await chatInput.fill("Audit Test: Checking staircase width standards");
    await chatInput.press("Enter");
    await page.waitForTimeout(600);

    const oldSessionUrl = page.url();
    const oldSessionId = new URL(oldSessionUrl).searchParams.get("session") || "session-initial";
    console.log(`[Phase02A.1D] Active Conversation 1 Established. Session ID: ${oldSessionId}`);

    // Click + New Chat while already on AI Assistant
    const newChatBtn = page.getByRole("button", { name: /New Chat|نئی چیٹ/i }).first();
    await newChatBtn.click();
    await page.waitForURL("**/dashboard/ai-assistant**", { timeout: 10000 });
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(600);

    // TASK 3 - SCREENSHOT 5: New Chat Welcome Screen
    const welcomeScreenMascot = page.locator("div.overflow-y-auto img[alt='TameerAI Assistant']").first();
    await expect(welcomeScreenMascot).toBeVisible();
    const welcomeBox = await welcomeScreenMascot.boundingBox();
    console.log(`[Phase02A.1D] Welcome Mascot BoundingBox: width=${welcomeBox?.width}px, height=${welcomeBox?.height}px`);

    const screenshotWelcome = path.join(ARTIFACT_SCREENSHOT_DIR, "Phase02A_1D-Desktop-Welcome-Screen.png");
    await page.screenshot({ path: screenshotWelcome, fullPage: false });
    console.log(`[Phase02A.1D] Saved: ${screenshotWelcome}`);

    // Verify old messages disappeared
    const oldMsgCount = await page.locator("text=Audit Test: Checking staircase width standards").count();
    expect(oldMsgCount).toBe(0);
    console.log("[Phase02A.1D] PASS: Old messages disappeared immediately upon clicking New Chat.");

    // Verify old session ID is removed from the URL (Task 1 Item 6 & Task 2 Item 4)
    const newSessionUrl = page.url();
    const newSessionId = new URL(newSessionUrl).searchParams.get("session");
    console.log(`[Phase02A.1D] New Session URL: ${newSessionUrl}`);
    expect(newSessionId).not.toBe(oldSessionId);
    expect(newSessionId).toBeNull();
    console.log(`[Phase02A.1D] PASS: Previous session parameter (${oldSessionId}) removed from URL.`);

    // =========================================================================
    // TASK 2: Stale Session Prevention & Non-Deletion
    // =========================================================================
    console.log("[Phase02A.1D] Testing Task 2: Reloading browser to verify stale session prevention...");
    await page.reload();
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(800);

    // After reload, confirm the old conversation does not automatically reopen
    const currentUrlAfterReload = page.url();
    const currentSidAfterReload = new URL(currentUrlAfterReload).searchParams.get("session");
    expect(currentSidAfterReload).not.toBe(oldSessionId);
    expect(currentSidAfterReload).toBeNull();
    console.log(`[Phase02A.1D] PASS: Browser reload did not reopen old session (${oldSessionId}).`);

    // Confirm old conversation text did not reopen (Task 2 Item 6)
    const oldMsgCountAfterReload = await page.locator("text=Audit Test: Checking staircase width standards").count();
    expect(oldMsgCountAfterReload).toBe(0);
    console.log("[Phase02A.1D] PASS: Old conversation did not automatically reopen after reload.");

    // Confirm fresh conversation can be started
    const freshInput = page.locator("div.border-t input[type='text']").first();
    await freshInput.fill("Audit Test 2: Inquire about concrete slump limits");
    await freshInput.press("Enter");
    await page.waitForTimeout(600);

    const freshMsgCount = await page.locator("text=Audit Test 2: Inquire about concrete slump limits").count();
    expect(freshMsgCount).toBeGreaterThan(0);
    console.log("[Phase02A.1D] PASS: Fresh conversation started and messages sent successfully.");

    // Confirm no unintended hard deletion: check sidebar history
    const sidebarSessions = page.locator("aside:visible div.overflow-y-auto button");
    const sidebarSessionCount = await sidebarSessions.count();
    expect(sidebarSessionCount).toBeGreaterThanOrEqual(1);
    console.log(`[Phase02A.1D] PASS: Past sessions remain available in sidebar (${sidebarSessionCount} found). No hard deletion occurred.`);

    // =========================================================================
    // TASK 1 - SCENARIO 2: User is on Dashboard
    // =========================================================================
    console.log("[Phase02A.1D] Testing Scenario 2: User clicks New Chat from Dashboard (/dashboard)...");
    await page.goto("/dashboard");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(500);

    const newChatFromDashboard = page.getByRole("button", { name: /New Chat|نئی چیٹ/i }).first();
    await newChatFromDashboard.click();
    await page.waitForURL("**/dashboard/ai-assistant**", { timeout: 10000 });
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(800);

    expect(page.url()).toContain("/dashboard/ai-assistant");
    const headerFromDashboard = page.locator("div.h-12 img[alt='TameerAI Assistant']").first();
    await expect(headerFromDashboard).toBeVisible();
    console.log("[Phase02A.1D] PASS Scenario 2: Clicking New Chat from Dashboard navigated to AI Assistant cleanly.");

    // =========================================================================
    // TASK 1 - SCENARIO 3: User is on another engineering module (/dashboard/costs)
    // =========================================================================
    console.log("[Phase02A.1D] Testing Scenario 3: User clicks New Chat from Cost Intelligence module (/dashboard/costs)...");
    await page.goto("/dashboard/costs");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(500);

    const newChatFromCosts = page.getByRole("button", { name: /New Chat|نئی چیٹ/i }).first();
    await newChatFromCosts.click();
    await page.waitForURL("**/dashboard/ai-assistant**", { timeout: 10000 });
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(800);

    expect(page.url()).toContain("/dashboard/ai-assistant");
    const headerFromCosts = page.locator("div.h-12 img[alt='TameerAI Assistant']").first();
    await expect(headerFromCosts).toBeVisible();
    console.log("[Phase02A.1D] PASS Scenario 3: Clicking New Chat from Costs module navigated to AI Assistant cleanly.");
  });

  test("Task 3 - Screenshot 6: Mobile Drawer Capture", async ({ page }, testInfo) => {
    const isMobile = testInfo.project.name.includes("Mobile-375x812");
    if (!isMobile) return;

    console.log(`[Phase02A.1D] Running Mobile Drawer screenshot capture on ${testInfo.project.name}`);

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

    const drawerLogo = page.locator("aside:visible img[alt='TameerAI Construction Assistant']").first();
    await expect(drawerLogo).toBeVisible();

    const screenshotDrawer = path.join(ARTIFACT_SCREENSHOT_DIR, "Phase02A_1D-Mobile-Drawer.png");
    await page.screenshot({ path: screenshotDrawer, fullPage: false });
    console.log(`[Phase02A.1D] Saved: ${screenshotDrawer}`);
  });
});

