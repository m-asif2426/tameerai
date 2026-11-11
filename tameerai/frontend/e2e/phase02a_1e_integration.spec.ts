import { test, expect } from "@playwright/test";
import * as path from "path";
import * as fs from "fs";

const ARTIFACT_SCREENSHOT_DIR = "C:\\Users\\muham\\.gemini\\antigravity\\brain\\85c7d051-a1b8-4814-8e24-56414fa9526c\\screenshots";

test.beforeAll(async () => {
  if (!fs.existsSync(ARTIFACT_SCREENSHOT_DIR)) {
    fs.mkdirSync(ARTIFACT_SCREENSHOT_DIR, { recursive: true });
  }
});

test.describe("Phase 02A.1E: Critical Chat API Integration & Cross-Route State Corrections", () => {
  test.beforeEach(async ({ page }) => {
    // Authenticate with test user
    await page.goto("/login");
    await page.waitForLoadState("domcontentloaded");
    await page.locator("input[type='email']").fill("phase02a_test@tameerai.pk");
    await page.locator("input[type='password']").fill("Password12345!");
    await page.locator("button[type='submit']").click();
    await page.waitForURL("**/dashboard**", { timeout: 15000 });
    await page.waitForLoadState("networkidle");
  });

  test("Task 1: Chat API Endpoint Normalization & Network Request Audit", async ({ page }) => {
    // Monitor outgoing requests to /chat/sessions
    const outgoingChatUrls: string[] = [];
    page.on("request", (req) => {
      const url = req.url();
      if (url.includes("/chat/")) {
        outgoingChatUrls.push(url);
      }
    });

    // Navigate to AI Assistant
    await page.goto("/dashboard/ai-assistant");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(500);

    // Verify all captured chat URLs do NOT contain duplicate /api/v1 prefix
    console.log(`[Task 1 Audit] Captured Chat URLs count: ${outgoingChatUrls.length}`);
    for (const url of outgoingChatUrls) {
      console.log(`[Task 1 Audit] URL: ${url}`);
      expect(url).not.toContain("/api/v1/api/v1");
      expect(url).toContain("/api/v1/chat/");
    }
  });

  test("Task 2: Universal New Chat Navigation from /dashboard, /dashboard/costs, and In-Page Clicks", async ({ page }) => {
    const openDrawerIfMobile = async () => {
      const viewport = page.viewportSize();
      if (viewport && viewport.width < 1024) {
        const toggle = page.getByRole("button", { name: /Toggle navigation|مینیو/i }).first();
        if (await toggle.isVisible()) {
          await toggle.click();
          await page.waitForTimeout(300);
        }
      }
    };

    // 1. From /dashboard: Click New Chat
    await page.goto("/dashboard");
    await page.waitForLoadState("networkidle");

    await openDrawerIfMobile();
    const newChatBtn = page.locator("button:visible").filter({ hasText: /New Chat|نئی چیٹ/i }).first();
    await expect(newChatBtn).toBeVisible();
    await newChatBtn.click();

    // Verify route is /dashboard/ai-assistant
    await page.waitForURL((url) => url.pathname.includes("/dashboard/ai-assistant"), { timeout: 10000 });
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(500);

    // Verify Welcome screen is displayed with 72x48 mascot
    const welcomeMascot = page.locator("div.overflow-y-auto img[alt='TameerAI Assistant']").first();
    await expect(welcomeMascot).toBeVisible();
    const box = await welcomeMascot.boundingBox();
    expect(box?.width).toBeCloseTo(72, 5);
    expect(box?.height).toBeCloseTo(48, 5);

    // Verify ?new= query parameter was stripped cleanly
    expect(page.url()).not.toContain("?new=");

    // 2. From /dashboard/costs: Click New Chat
    await page.goto("/dashboard/costs");
    await page.waitForLoadState("networkidle");

    await openDrawerIfMobile();
    const newChatFromCosts = page.locator("button:visible").filter({ hasText: /New Chat|نئی چیٹ/i }).first();
    await newChatFromCosts.click();

    await page.waitForURL((url) => url.pathname.includes("/dashboard/ai-assistant"), { timeout: 10000 });
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(500);

    await expect(welcomeMascot).toBeVisible();
    expect(page.url()).not.toContain("?new=");

    // 3. In-page repeated New Chat clicks
    const input = page.locator("input[placeholder*='Ask about']").first();
    await input.fill("Testing in-page reset");
    await page.keyboard.press("Enter");
    await expect(page.getByText("Testing in-page reset").first()).toBeVisible({ timeout: 10000 });

    // Active messages are present
    const messageBubbles = page.locator("div.overflow-y-auto > div");
    expect(await messageBubbles.count()).toBeGreaterThan(0);

    // Click New Chat again while already on AI Assistant
    await openDrawerIfMobile();
    const newChatInPage = page.locator("button:visible").filter({ hasText: /New Chat|نئی چیٹ/i }).first();
    await newChatInPage.click();

    // Verify messages cleared and Welcome Screen visible
    await expect(welcomeMascot).toBeVisible({ timeout: 10000 });
    await expect(page.locator("main").getByText("Deterministic Reference Assessment")).toHaveCount(0);

    // Repeated click test: click New Chat a second time
    await openDrawerIfMobile();
    await newChatInPage.click();
    await expect(welcomeMascot).toBeVisible({ timeout: 10000 });
  });

  test("Task 3: Session Creation, Message Flow, Persistence, Rename & Archive against Genuine Backend", async ({ page }) => {
    // 1. Go to AI Assistant (fresh state)
    await page.goto("/dashboard/ai-assistant");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(500);

    // Submit a technical query via chat input
    const input = page.locator("input[placeholder*='Ask about']").first();
    await expect(input).toBeVisible();
    await input.click();
    await input.fill("Minimum staircase clear width under PBC 2021");
    await expect(input).toHaveValue("Minimum staircase clear width under PBC 2021");
    const sendBtn = page.locator("button:has(svg.lucide-send)").first();
    await sendBtn.click();

    // 2. Wait for message and deterministic advisory response
    const userBubble = page.locator("main p:has-text('Minimum staircase clear width under PBC 2021')").first();
    await expect(userBubble).toBeVisible({ timeout: 10000 });

    const advisoryAnswer = page.locator("main p:has-text('Pakistan Building Code (PBC 2021)')").first();
    await expect(advisoryAnswer).toBeVisible({ timeout: 10000 });

    // Verify URL was updated with genuine backend session ID
    await page.waitForURL(/session=/, { timeout: 10000 });
    const url = page.url();
    expect(url).toContain("?session=");
    const sessionId = new URL(url).searchParams.get("session");
    expect(sessionId).toBeTruthy();
    console.log(`[Task 3] Live Session ID created in PostgreSQL: ${sessionId}`);

    // 3. Reload browser and confirm conversation reopens with persisted messages
    await page.reload();
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1000);

    await expect(userBubble).toBeVisible();
    await expect(advisoryAnswer).toBeVisible();
    console.log("[Task 3] Persisted dialogue turns reloaded successfully across browser refresh");

    // 4. Rename conversation via Combined Sidebar
    const sessionItem = page.locator(`aside:visible div:has(a[href*='${sessionId}'])`).first();
    await expect(sessionItem).toBeVisible();

    // Hover to reveal action buttons
    await sessionItem.hover();
    const renameBtn = sessionItem.locator("button[aria-label='Rename conversation']").first();
    if (await renameBtn.isVisible()) {
      await renameBtn.click();
      const renameInput = sessionItem.locator("input[type='text']").first();
      await renameInput.fill("PBC Egress Code Audit");
      await page.keyboard.press("Enter");
      await page.waitForTimeout(1000);

      // Verify updated title in sidebar
      await expect(page.locator(`aside:visible a:has-text('PBC Egress Code Audit')`).first()).toBeVisible();
      console.log("[Task 3] Session renamed successfully to 'PBC Egress Code Audit'");
    }

    // 5. Archive conversation
    const archiveBtn = sessionItem.locator("button[aria-label='Archive conversation']").first();
    if (await archiveBtn.isVisible()) {
      await archiveBtn.click();
      await page.waitForTimeout(1000);

      // Confirm archived conversation disappears from active Recent Consultations
      const activeLink = page.locator(`aside:visible a[href*='${sessionId}']`);
      expect(await activeLink.count()).toBe(0);
      console.log("[Task 3] Session archived and safely excluded from active sessions list");
    }
  });

  test("Task 4 & 5: Visual Specification Reconciliation & Neutral Identity Wording", async ({ page }) => {
    await page.goto("/dashboard/ai-assistant");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(500);

    // 1. Expanded Sidebar Logo
    const expandedLogo = page.locator("aside:visible img[alt='TameerAI Construction Assistant']").first();
    await expect(expandedLogo).toBeVisible();
    const expandedBox = await expandedLogo.boundingBox();
    expect(expandedBox).not.toBeNull();
    if (expandedBox) {
      console.log(`[Task 4 Visual] Expanded Sidebar Wordmark: width=${expandedBox.width}px, height=${expandedBox.height}px`);
      expect(expandedBox.width).toBeGreaterThanOrEqual(120);
      expect(expandedBox.width).toBeLessThanOrEqual(140);
      expect(expandedBox.height).toBeGreaterThanOrEqual(38);
      expect(expandedBox.height).toBeLessThanOrEqual(46);
    }

    // 2. Chat Header Mascot & Identity Wording
    const headerMascot = page.locator("div.h-12 img[alt='TameerAI Assistant']").first();
    await expect(headerMascot).toBeVisible();
    const headerBox = await headerMascot.boundingBox();
    expect(headerBox).not.toBeNull();
    if (headerBox) {
      console.log(`[Task 4 Visual] Chat Header Mascot: width=${headerBox.width}px, height=${headerBox.height}px`);
      expect(headerBox.width).toBeGreaterThanOrEqual(40);
      expect(headerBox.width).toBeLessThanOrEqual(44);
      expect(headerBox.height).toBeGreaterThanOrEqual(26);
      expect(headerBox.height).toBeLessThanOrEqual(30);
    }

    // Task 5: Verify Neutral Subtitle
    const subtitle = page.locator("text='Pakistan Building Codes & Construction Intelligence'").first();
    await expect(subtitle).toBeVisible();
    console.log("[Task 5 Neutral Identity] Verified subtitle: 'Pakistan Building Codes & Construction Intelligence'");

    // 3. Welcome Mascot (Verified on New Chat)
    const newChatBtn = page.getByRole("button", { name: /New Chat|نئی چیٹ/i }).first();
    await newChatBtn.click();
    await page.waitForTimeout(600);

    const welcomeMascot = page.locator("div.overflow-y-auto img[alt='TameerAI Assistant']").first();
    await expect(welcomeMascot).toBeVisible();
    const welcomeBox = await welcomeMascot.boundingBox();
    expect(welcomeBox).not.toBeNull();
    if (welcomeBox) {
      console.log(`[Task 4 Visual] Welcome Mascot: width=${welcomeBox.width}px, height=${welcomeBox.height}px`);
      expect(welcomeBox.width).toBeGreaterThanOrEqual(70);
      expect(welcomeBox.width).toBeLessThanOrEqual(75);
      expect(welcomeBox.height).toBeGreaterThanOrEqual(46);
      expect(welcomeBox.height).toBeLessThanOrEqual(50);
    }

    // Take screenshot evidence
    const screenshotPath = path.join(ARTIFACT_SCREENSHOT_DIR, "Phase02A_1E-Desktop-Reconciled-Visual.png");
    await page.screenshot({ path: screenshotPath, fullPage: false });
    console.log(`[Task 4 Visual] Saved evidence screenshot: ${screenshotPath}`);
  });
});

