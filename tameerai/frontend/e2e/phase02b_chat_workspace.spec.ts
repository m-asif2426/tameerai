import { test, expect } from "@playwright/test";
import * as path from "path";
import * as fs from "fs";

const ARTIFACT_SCREENSHOT_DIR = "C:\\Users\\muham\\.gemini\\antigravity\\brain\\85c7d051-a1b8-4814-8e24-56414fa9526c\\screenshots";

const openDrawerIfMobile = async (page: any) => {
  const viewport = page.viewportSize();
  if (viewport && viewport.width < 1024) {
    const toggle = page.locator("button[aria-label='Toggle navigation']").first();
    if (await toggle.isVisible()) {
      await toggle.click();
      await page.waitForTimeout(300);
    }
  }
};

test.beforeAll(async () => {
  if (!fs.existsSync(ARTIFACT_SCREENSHOT_DIR)) {
    fs.mkdirSync(ARTIFACT_SCREENSHOT_DIR, { recursive: true });
  }
});

test.describe("Phase 02B: Modular Chat Workspace & Six Engineering Shortcuts", () => {
  test.beforeEach(async ({ page }) => {
    // Authenticate with test credentials
    await page.goto("/login");
    await page.waitForLoadState("domcontentloaded");
    await page.locator("input[type='email']").fill("phase02a_test@tameerai.pk");
    await page.locator("input[type='password']").fill("Password12345!");
    await page.locator("button[type='submit']").click();
    await page.waitForURL("**/dashboard**", { timeout: 15000 });
    await page.waitForLoadState("networkidle");
  });

  test("Task 1 & 2: Welcome Screen Architecture & Mascot Sizing", async ({ page }) => {
    await page.goto("/dashboard/ai-assistant");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(500);

    // 1. Welcome Mascot (72x48)
    const welcomeMascot = page.locator("div.overflow-y-auto img[alt='TameerAI Assistant']").first();
    await expect(welcomeMascot).toBeVisible();
    const box = await welcomeMascot.boundingBox();
    expect(box).not.toBeNull();
    if (box) {
      console.log(`[Task 1] Welcome Mascot rendered dimensions: ${box.width}x${box.height}px`);
      expect(box.width).toBeGreaterThanOrEqual(70);
      expect(box.width).toBeLessThanOrEqual(74);
      expect(box.height).toBeGreaterThanOrEqual(46);
      expect(box.height).toBeLessThanOrEqual(50);
    }

    // 2. Main Heading and Subtitle
    await expect(page.locator("h2:has-text('How can TameerAI help you today?')")).toBeVisible();
    await expect(page.locator("p:has-text('Your construction and engineering intelligence workspace.')")).toBeVisible();

    // 3. Header Mascot (42x28)
    const headerMascot = page.locator("div.h-12 img[alt='TameerAI Assistant']").first();
    await expect(headerMascot).toBeVisible();
    const headerBox = await headerMascot.boundingBox();
    expect(headerBox).not.toBeNull();
    if (headerBox) {
      console.log(`[Task 1] Header Mascot rendered dimensions: ${headerBox.width}x${headerBox.height}px`);
      expect(headerBox.width).toBeGreaterThanOrEqual(40);
      expect(headerBox.width).toBeLessThanOrEqual(44);
      expect(headerBox.height).toBeGreaterThanOrEqual(26);
      expect(headerBox.height).toBeLessThanOrEqual(30);
    }

    // 4. Header Identity and Subtitle
    await expect(page.locator("div.h-12 span:has-text('TameerAI Assistant')")).toBeVisible();
    await expect(page.locator("div.h-12 span:has-text('Construction Intelligence Workspace')")).toBeVisible();

    // 5. Capability Disclosure Notice (No PEC accreditation claim)
    const disclosure = page.locator("div.overflow-y-auto").getByText(/Current mode: Deterministic engineering guidance/i).first();
    await expect(disclosure).toBeVisible();

    // Confirm NO false PEC verification/accreditation claims
    const pageText = await page.locator("main").innerText();
    expect(pageText).not.toContain("Verified PEC Engineer");
    expect(pageText).not.toContain("PEC License #");

    // Take Desktop Welcome Screen Screenshot
    const screenshotPath = path.join(ARTIFACT_SCREENSHOT_DIR, "Phase02B-Desktop-Welcome-Screen.png");
    await page.screenshot({ path: screenshotPath });
    console.log(`[Screenshot Evidence] Saved: ${screenshotPath}`);
  });

  test("Task 3: Six Engineering Shortcut Cards Exact Destinations & Visual State", async ({ page }) => {
    await page.goto("/dashboard/ai-assistant");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(500);

    const shortcuts = [
      {
        title: "BOQ & Cost Estimation",
        href: "/dashboard/costs",
        description: "Explore available construction cost intelligence tools.",
      },
      {
        title: "Structural Safety",
        href: "/dashboard/safety",
        description: "Access structural safety assessment and available hazard indicators.",
      },
      {
        title: "Building Regulations",
        href: "/dashboard/regulations",
        description: "Explore available building regulations and compliance information.",
      },
      {
        title: "Material Market Rates",
        href: "/dashboard/costs",
        description: "Explore available material prices, grades and source information.",
      },
      {
        title: "Contract Analysis",
        href: "/dashboard/contracts",
        description: "Open the existing construction contract workspace.",
      },
      {
        title: "Project Planning",
        href: "/dashboard/projects",
        description: "Explore your existing projects and available project information.",
      },
    ];

    // Verify all 6 cards exist with correct hrefs
    const cards = page.locator("a[id^='shortcut-']");
    expect(await cards.count()).toBe(6);

    for (let i = 0; i < shortcuts.length; i++) {
      const shortcut = shortcuts[i];
      const card = cards.nth(i);
      await expect(card).toBeVisible();

      // Verify title and description
      await expect(card.locator("h3, h4")).toHaveText(shortcut.title);
      await expect(card.locator("p")).toHaveText(shortcut.description);

      // Verify href
      const href = await card.getAttribute("href");
      expect(href).toBe(shortcut.href);
    }

    // Verify clicking a card navigates directly to the module without submitting a prompt
    const boqCard = cards.first();
    await boqCard.click();
    await page.waitForURL("**/dashboard/costs**", { timeout: 10000 });
    expect(page.url()).toContain("/dashboard/costs");
  });

  test("Task 4: Active Conversation Toggling & New Chat Reset", async ({ page }) => {
    await page.goto("/dashboard/ai-assistant");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(500);

    // Initial state: Welcome Screen is shown, 6 cards present
    const cards = page.locator("a[id^='shortcut-']");
    expect(await cards.count()).toBe(6);

    // Send a message via input bar
    const input = page.locator("input[placeholder*='Ask about']").first();
    await input.fill("What is the minimum staircase clear width under PBC 2021?");
    const sendBtn = page.locator("button:has(svg.lucide-send)").first();
    await sendBtn.click();

    // Verify 6 cards disappear
    await expect(page.locator("a[id^='shortcut-']")).toHaveCount(0);

    // Verify message stream appears
    const userBubble = page.locator("main p:has-text('What is the minimum staircase clear width under PBC 2021?')").first();
    await expect(userBubble).toBeVisible({ timeout: 10000 });

    const assistantAvatar = page.locator("main img[alt='TameerAI'][width='40']").first();
    await expect(assistantAvatar).toBeVisible({ timeout: 10000 });
    await page.waitForTimeout(600);
    await assistantAvatar.scrollIntoViewIfNeeded();
    const avatarBox = await assistantAvatar.boundingBox();
    expect(avatarBox).not.toBeNull();
    if (avatarBox) {
      console.log(`[Task 4] Assistant Turn Mascot dimensions: ${avatarBox.width}x${avatarBox.height}px`);
      expect(avatarBox.width).toBeGreaterThanOrEqual(38);
      expect(avatarBox.width).toBeLessThanOrEqual(42);
      expect(avatarBox.height).toBeGreaterThanOrEqual(25);
      expect(avatarBox.height).toBeLessThanOrEqual(29);
    }

    // Take Desktop Active Conversation Screenshot
    const convoScreenshotPath = path.join(ARTIFACT_SCREENSHOT_DIR, "Phase02B-Desktop-Active-Conversation.png");
    await page.screenshot({ path: convoScreenshotPath });
    console.log(`[Screenshot Evidence] Saved: ${convoScreenshotPath}`);

    // Click New Chat to reset
    await openDrawerIfMobile(page);
    const newChatBtn = page.locator("button:visible").filter({ hasText: /New Chat|نئی چیٹ/i }).first();
    await newChatBtn.click();
    await page.waitForTimeout(500);

    // Verify Welcome Screen returns with all 6 cards
    await expect(page.locator("a[id^='shortcut-']")).toHaveCount(6);
    await expect(page.locator("h2:has-text('How can TameerAI help you today?')")).toBeVisible();
  });

  test("Task 5: Responsive Verification (Laptop, Tablet, Mobile) & Drawer Integrity", async ({ page }) => {
    // 1. Laptop (1366x768)
    await page.setViewportSize({ width: 1366, height: 768 });
    await page.goto("/dashboard/ai-assistant");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("a[id^='shortcut-']")).toHaveCount(6);

    const laptopPath = path.join(ARTIFACT_SCREENSHOT_DIR, "Phase02B-Laptop-Welcome-Screen.png");
    await page.screenshot({ path: laptopPath });
    console.log(`[Screenshot Evidence] Saved: ${laptopPath}`);

    // 2. Tablet (768x1024)
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto("/dashboard/ai-assistant");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("a[id^='shortcut-']")).toHaveCount(6);

    const tabletPath = path.join(ARTIFACT_SCREENSHOT_DIR, "Phase02B-Tablet-Welcome-Screen.png");
    await page.screenshot({ path: tabletPath });
    console.log(`[Screenshot Evidence] Saved: ${tabletPath}`);

    // 3. Mobile (375x812)
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto("/dashboard/ai-assistant");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("a[id^='shortcut-']")).toHaveCount(6);

    const mobilePath = path.join(ARTIFACT_SCREENSHOT_DIR, "Phase02B-Mobile-Welcome-Screen.png");
    await page.screenshot({ path: mobilePath });
    console.log(`[Screenshot Evidence] Saved: ${mobilePath}`);

    // Open Mobile Drawer and capture
    const drawerToggle = page.locator("button[aria-label='Toggle navigation']").first();
    await drawerToggle.click();
    await page.waitForTimeout(400);

    const mobileDrawerPath = path.join(ARTIFACT_SCREENSHOT_DIR, "Phase02B-Mobile-Drawer-Open.png");
    await page.screenshot({ path: mobileDrawerPath });
    console.log(`[Screenshot Evidence] Saved: ${mobileDrawerPath}`);
  });

  test("Task 6: Urdu RTL Localization & Sidebar Expansion/Collapse Screenshots", async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto("/dashboard/ai-assistant");
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(500);

    // 1. Desktop Expanded Sidebar Screenshot
    const expandedScreenshotPath = path.join(ARTIFACT_SCREENSHOT_DIR, "Phase02B-Desktop-Expanded-Sidebar.png");
    await page.screenshot({ path: expandedScreenshotPath });
    console.log(`[Screenshot Evidence] Saved: ${expandedScreenshotPath}`);

    // 2. Desktop Collapsed Sidebar Screenshot
    const collapseBtn = page.locator("button[aria-label='Collapse Sidebar']").first();
    await collapseBtn.click();
    await page.waitForTimeout(500);

    const collapsedScreenshotPath = path.join(ARTIFACT_SCREENSHOT_DIR, "Phase02B-Desktop-Collapsed-Sidebar.png");
    await page.screenshot({ path: collapsedScreenshotPath });
    console.log(`[Screenshot Evidence] Saved: ${collapsedScreenshotPath}`);

    // Expand sidebar back
    const expandBtn = page.locator("button[aria-label='Expand Sidebar']").first();
    await expandBtn.click();
    await page.waitForTimeout(500);

    // 3. Toggle Language to Urdu (RTL)
    const langBtn = page.locator("button[title='Toggle English / اردو']").first();
    await langBtn.click();
    await page.waitForTimeout(500);

    // Verify Urdu Welcome Heading & Shortcut Card
    await expect(page.locator("h2:has-text('آج تعمیر اے آئی آپ کی کیا مدد کر سکتا ہے؟')")).toBeVisible();
    await expect(page.locator("h3, h4").filter({ hasText: "بی او کیو اور لاگت کا تخمینہ" })).toBeVisible();

    // Capture Urdu RTL Screenshot
    const urduScreenshotPath = path.join(ARTIFACT_SCREENSHOT_DIR, "Phase02B-Urdu-RTL-Welcome.png");
    await page.screenshot({ path: urduScreenshotPath });
    console.log(`[Screenshot Evidence] Saved: ${urduScreenshotPath}`);

    // Restore back to English
    await langBtn.click();
    await page.waitForTimeout(300);
  });
});
