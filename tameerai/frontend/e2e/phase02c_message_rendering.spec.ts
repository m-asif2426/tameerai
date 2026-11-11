import { test, expect } from "@playwright/test";
import * as path from "path";
import * as fs from "fs";

const ARTIFACT_SCREENSHOT_DIR = "C:\\Users\\muham\\.gemini\\antigravity\\brain\\85c7d051-a1b8-4814-8e24-56414fa9526c\\screenshots";

const safeScroll = async (page: any, locator: any) => {
  await page.waitForTimeout(500);
  try {
    await locator.first().scrollIntoViewIfNeeded({ timeout: 3000 });
  } catch {
    // Ignore transient DOM unmount during session synchronization reflow
  }
};

test.beforeAll(async () => {
  if (!fs.existsSync(ARTIFACT_SCREENSHOT_DIR)) {
    fs.mkdirSync(ARTIFACT_SCREENSHOT_DIR, { recursive: true });
  }
});

test.describe("Phase 02C: Professional Message Rendering & Engineering Presentation", () => {
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

  test("Task 1: Detailed Step-by-Step Calculation Block Rendering (All 10 Elements)", async ({ page }) => {
    await page.goto(`/dashboard/ai-assistant?new=${Date.now()}`);
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(500);

    // Ask calculation query: Concrete slab volume & materials
    const input = page.locator("input[placeholder*='Ask about']").first();
    await input.fill("Calculate concrete slab volume and materials for 30ft x 20ft x 6in");
    const sendBtn = page.locator("button:has(svg.lucide-send)").first();
    await sendBtn.click();

    // Verify calculation block appears
    const calcBlock = page.locator("[data-testid='calculation-block']").first();
    await expect(calcBlock).toBeVisible({ timeout: 12000 });
    await safeScroll(page, calcBlock);

    // 1. Title
    await expect(calcBlock.locator("h4:has-text('Reinforced Concrete Slab Volume')").first()).toBeVisible();

    // 2. Input Parameters Table
    const inputTable = calcBlock.locator("[data-testid='message-table-container']").first();
    await expect(inputTable).toBeVisible();
    await expect(inputTable.locator("th:has-text('Parameter')").first()).toBeVisible();
    await expect(inputTable.locator("td:has-text('Clear structural span')").first()).toBeVisible();

    // 3. Governing Formula
    const formulaBlock = calcBlock.locator("[data-testid='formula-block']").first();
    await expect(formulaBlock).toBeVisible();

    // 4. Variable Definitions
    await expect(calcBlock.getByText(/Variable Definitions/i).first()).toBeVisible();
    await expect(calcBlock.locator("li:has-text('Length of slab')").first()).toBeVisible();

    // 5. Numerical Substitution
    await expect(calcBlock.getByText(/Numerical Substitution/i).first()).toBeVisible();
    await expect(calcBlock.locator("div:has-text('30.0')").first()).toBeVisible();

    // 6. Intermediate Steps
    await expect(calcBlock.getByText(/Intermediate Calculations/i).first()).toBeVisible();
    await expect(calcBlock.locator("li:has-text('300.00 cu ft')").first()).toBeVisible();
    await expect(calcBlock.locator("li:has-text('67.2 bags')").first()).toBeVisible();

    // 7. Final Computed Result
    await expect(calcBlock.getByText(/Final Computed Result/i).first()).toBeVisible();
    await expect(calcBlock.locator("span:has-text('11.11')").first()).toBeVisible();
    await expect(calcBlock.locator("span:has-text('yd³')").first()).toBeVisible();

    // 8. Assumptions
    await expect(calcBlock.getByText(/Assumptions/i).first()).toBeVisible();
    await expect(calcBlock.locator("li:has-text('Class M20')").first()).toBeVisible();

    // 9. Limitations
    await expect(calcBlock.getByText(/Limitations/i).first()).toBeVisible();
    await expect(calcBlock.locator("li:has-text('formwork deflection')").first()).toBeVisible();

    // 10. Engineering Recommendation
    await expect(calcBlock.getByText(/Recommendation/i).first()).toBeVisible();
    await expect(calcBlock.locator("div:has-text('12.0 cubic yards')").first()).toBeVisible();

    // Copy calculation action
    const copyCalcBtn = calcBlock.locator("button[aria-label='Copy calculation']").first();
    await expect(copyCalcBtn).toBeVisible();
    await copyCalcBtn.click();
    await expect(calcBlock.locator("span:has-text('Copied')").first()).toBeVisible();

    // Save screenshot evidence
    const screenshotPath = path.join(ARTIFACT_SCREENSHOT_DIR, "Phase02C-Desktop-Calculation-Block.png");
    await page.screenshot({ path: screenshotPath });
    console.log(`[Screenshot Evidence] Saved: ${screenshotPath}`);
  });

  test("Task 2: Mathematical Formula Block Rendering (Inline & Block)", async ({ page }) => {
    await page.goto(`/dashboard/ai-assistant?new=${Date.now()}`);
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(500);

    const input = page.locator("input[placeholder*='Ask about']").first();
    await input.fill("Calculate concrete slab volume");
    const sendBtn = page.locator("button:has(svg.lucide-send)").first();
    await sendBtn.click();

    // Locate formula block
    const formulaBlock = page.locator("[data-testid='formula-block']").first();
    await expect(formulaBlock).toBeVisible({ timeout: 12000 });
    await safeScroll(page, formulaBlock);

    // Check accessibility attribute
    const roleAttr = await formulaBlock.getAttribute("role");
    expect(roleAttr).toBe("math");

    // Check fraction rendering (vertical fraction bar)
    const fracEl = formulaBlock.locator("span.inline-flex.flex-col").first();
    await expect(fracEl).toBeVisible();

    // Save screenshot evidence
    const screenshotPath = path.join(ARTIFACT_SCREENSHOT_DIR, "Phase02C-Desktop-Formula-Block.png");
    await page.screenshot({ path: screenshotPath });
    console.log(`[Screenshot Evidence] Saved: ${screenshotPath}`);
  });

  test("Task 3: Engineering Table Rendering & Data Copying", async ({ page }) => {
    await page.goto(`/dashboard/ai-assistant?new=${Date.now()}`);
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(500);

    // Send query for concrete mix specifications
    const input = page.locator("input[placeholder*='Ask about']").first();
    await input.fill("What are standard concrete mix ratios M20 and M25?");
    const sendBtn = page.locator("button:has(svg.lucide-send)").first();
    await sendBtn.click();

    const tableContainer = page.locator("[data-testid='message-table-container']").first();
    await expect(tableContainer).toBeVisible({ timeout: 12000 });
    await safeScroll(page, tableContainer);

    // Verify headers
    await expect(tableContainer.locator("th:has-text('Concrete Class')").first()).toBeVisible();
    await expect(tableContainer.locator("th:has-text('Volumetric Ratio')").first()).toBeVisible();
    await expect(tableContainer.locator("th:has-text('Target Strength')").first()).toBeVisible();

    // Verify row data
    await expect(tableContainer.locator("td:has-text('M20 (Class B)')").first()).toBeVisible();
    await expect(tableContainer.locator("td:has-text('1:1.5:3')").first()).toBeVisible();
    await expect(tableContainer.locator("td:has-text('3,000 psi')").first()).toBeVisible();

    // Test copy table action
    const copyTableBtn = tableContainer.locator("button[aria-label='Copy table data']").first();
    await expect(copyTableBtn).toBeVisible();
    await copyTableBtn.click();
    await expect(tableContainer.locator("span:has-text('Copied')").first()).toBeVisible();

    // Save screenshot evidence
    const screenshotPath = path.join(ARTIFACT_SCREENSHOT_DIR, "Phase02C-Desktop-Message-Table.png");
    await page.screenshot({ path: screenshotPath });
    console.log(`[Screenshot Evidence] Saved: ${screenshotPath}`);
  });

  test("Task 4: Structural Safety Notices & Clear Disclaimers", async ({ page }) => {
    await page.goto(`/dashboard/ai-assistant?new=${Date.now()}`);
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(500);

    // Egress question triggers warning safety notice
    const input = page.locator("input[placeholder*='Ask about']").first();
    await input.fill("What is the minimum staircase clear width under PBC 2021?");
    const sendBtn = page.locator("button:has(svg.lucide-send)").first();
    await sendBtn.click();

    const safetyNotice = page.locator("[data-testid='safety-notice-warning']").first();
    await expect(safetyNotice).toBeVisible({ timeout: 12000 });
    await safeScroll(page, safetyNotice);

    // Verify badge and title
    await expect(safetyNotice.locator("span:has-text('Compliance Warning')").first()).toBeVisible();
    await expect(safetyNotice.locator("h5:has-text('Municipal Plan Approval Non-Compliance')").first()).toBeVisible();

    // Verify code reference
    await expect(safetyNotice.getByText(/PBC 2021 Chapter 4/).first()).toBeVisible();

    // Verify transparent independent verification notice
    await expect(
      safetyNotice.getByText(/Does not replace mandatory physical inspection/i).first()
    ).toBeVisible();

    // Ensure NO fake certified PEC license stamp is claimed
    const noticeText = await safetyNotice.innerText();
    expect(noticeText).not.toContain("Verified PEC Clearance Stamp #");

    // Save screenshot evidence
    const screenshotPath = path.join(ARTIFACT_SCREENSHOT_DIR, "Phase02C-Desktop-Safety-Notices.png");
    await page.screenshot({ path: screenshotPath });
    console.log(`[Screenshot Evidence] Saved: ${screenshotPath}`);
  });

  test("Task 5: Statutory Citations List & Unverified Transparency", async ({ page }) => {
    await page.goto(`/dashboard/ai-assistant?new=${Date.now()}`);
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(500);

    const input = page.locator("input[placeholder*='Ask about']").first();
    await input.fill("What are minimum setbacks for 1 kanal plot?");
    const sendBtn = page.locator("button:has(svg.lucide-send)").first();
    await sendBtn.click();

    const citationList = page.locator("[data-testid='citation-list']").first();
    await expect(citationList).toBeVisible({ timeout: 12000 });
    await safeScroll(page, citationList);

    // Verify header
    await expect(
      citationList.getByText(/Regulatory References \(Subject to Independent Verification\)/i).first()
    ).toBeVisible();

    // Verify Unverified badge is clearly shown
    const unverifiedBadge = citationList.getByText(/UNVERIFIED - Subject to Source Verification/i).first();
    await expect(unverifiedBadge).toBeVisible();

    // Verify citation items
    const citationItem = page.locator("[data-testid='source-attribution-item']").first();
    await expect(citationItem).toBeVisible();
    await expect(citationItem.locator("span:has-text('CDA Building Regulations')").first()).toBeVisible();
    await expect(citationItem.getByText(/Doc: CDA-BR-2020/).first()).toBeVisible();
    await expect(citationItem.getByText(/Page 24/).first()).toBeVisible();

    // Copy citation reference
    const copyRefBtn = citationItem.locator("button[aria-label='Copy citation']").first();
    await expect(copyRefBtn).toBeVisible();
    await copyRefBtn.click();
    await expect(citationItem.locator("span:has-text('Copied')").first()).toBeVisible();

    // Save screenshot evidence
    const screenshotPath = path.join(ARTIFACT_SCREENSHOT_DIR, "Phase02C-Desktop-Citation-List.png");
    await page.screenshot({ path: screenshotPath });
    console.log(`[Screenshot Evidence] Saved: ${screenshotPath}`);
  });

  test("Task 6: Message Actions Toolbar (Copy & Feedback)", async ({ page }) => {
    await page.goto(`/dashboard/ai-assistant?new=${Date.now()}`);
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(500);

    const input = page.locator("input[placeholder*='Ask about']").first();
    await input.fill("What is the concrete mix ratio for M20?");
    const sendBtn = page.locator("button:has(svg.lucide-send)").first();
    await sendBtn.click();

    const actionsToolbar = page.locator("[data-testid='message-actions-toolbar']").first();
    await expect(actionsToolbar).toBeVisible({ timeout: 12000 });
    await safeScroll(page, actionsToolbar);

    // Copy action
    const copyBtn = actionsToolbar.locator("button[aria-label='Copy response to clipboard']").first();
    await expect(copyBtn).toBeVisible();
    await copyBtn.click();
    await expect(actionsToolbar.locator("span:has-text('Copied')").first()).toBeVisible();

    // Helpful feedback button
    const thumbsUpBtn = actionsToolbar.locator("button[aria-label='Helpful response']").first();
    await expect(thumbsUpBtn).toBeVisible();
    await thumbsUpBtn.click();

    // Verify compliance label
    await expect(actionsToolbar.getByText(/PBC 2021 Compliant/i).first()).toBeVisible();

    // Save screenshot evidence
    const screenshotPath = path.join(ARTIFACT_SCREENSHOT_DIR, "Phase02C-Desktop-Message-Actions.png");
    await page.screenshot({ path: screenshotPath });
    console.log(`[Screenshot Evidence] Saved: ${screenshotPath}`);
  });

  test("Task 7: Comprehensive Desktop Engineering Report Screenshot", async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto(`/dashboard/ai-assistant?new=${Date.now()}`);
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(500);

    const input = page.locator("input[placeholder*='Ask about']").first();
    await input.fill("Calculate concrete slab volume and materials for 30ft x 20ft x 6in");
    const sendBtn = page.locator("button:has(svg.lucide-send)").first();
    await sendBtn.click();

    await expect(page.locator("[data-testid='calculation-block']").first()).toBeVisible({ timeout: 12000 });
    await page.waitForTimeout(800);

    const screenshotPath = path.join(ARTIFACT_SCREENSHOT_DIR, "Phase02C-Desktop-Full-Report.png");
    await page.screenshot({ path: screenshotPath });
    console.log(`[Screenshot Evidence] Saved: ${screenshotPath}`);
  });

  test("Task 8: Laptop Responsive Viewport (1366x768)", async ({ page }) => {
    await page.setViewportSize({ width: 1366, height: 768 });
    await page.goto(`/dashboard/ai-assistant?new=${Date.now()}`);
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(500);

    const input = page.locator("input[placeholder*='Ask about']").first();
    await input.fill("Calculate concrete slab volume");
    const sendBtn = page.locator("button:has(svg.lucide-send)").first();
    await sendBtn.click();

    await expect(page.locator("[data-testid='calculation-block']").first()).toBeVisible({ timeout: 12000 });
    await page.waitForTimeout(600);

    const screenshotPath = path.join(ARTIFACT_SCREENSHOT_DIR, "Phase02C-Laptop-Responsive.png");
    await page.screenshot({ path: screenshotPath });
    console.log(`[Screenshot Evidence] Saved: ${screenshotPath}`);
  });

  test("Task 9: Tablet Responsive Viewport (768x1024)", async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto(`/dashboard/ai-assistant?new=${Date.now()}`);
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(500);

    const input = page.locator("input[placeholder*='Ask about']").first();
    await input.fill("Calculate concrete slab volume");
    const sendBtn = page.locator("button:has(svg.lucide-send)").first();
    await sendBtn.click();

    await expect(page.locator("[data-testid='calculation-block']").first()).toBeVisible({ timeout: 12000 });
    await page.waitForTimeout(600);

    const screenshotPath = path.join(ARTIFACT_SCREENSHOT_DIR, "Phase02C-Tablet-Responsive.png");
    await page.screenshot({ path: screenshotPath });
    console.log(`[Screenshot Evidence] Saved: ${screenshotPath}`);
  });

  test("Task 10: Mobile Responsive Viewport (375x812)", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto(`/dashboard/ai-assistant?new=${Date.now()}`);
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(500);

    const input = page.locator("input[placeholder*='Ask about']").first();
    await input.fill("Calculate concrete slab volume");
    const sendBtn = page.locator("button:has(svg.lucide-send)").first();
    await sendBtn.click();

    await expect(page.locator("[data-testid='calculation-block']").first()).toBeVisible({ timeout: 12000 });
    await page.waitForTimeout(600);

    const screenshotPath = path.join(ARTIFACT_SCREENSHOT_DIR, "Phase02C-Mobile-Responsive.png");
    await page.screenshot({ path: screenshotPath });
    console.log(`[Screenshot Evidence] Saved: ${screenshotPath}`);
  });

  test("Task 11: Urdu RTL Message Rendering", async ({ page }) => {
    // Set language to Urdu in localStorage prior to navigation
    await page.goto("/dashboard");
    await page.evaluate(() => {
      localStorage.setItem("tameerai-lang", "ur");
    });
    await page.goto(`/dashboard/ai-assistant?new=${Date.now()}`);
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(500);

    // Ask query in Urdu using dedicated composer locator
    const input = page.locator("input[placeholder*='پوچھیں'], input[placeholder*='Ask about']").first();
    await expect(input).toBeVisible();
    await input.fill("سلیب کے لیے کنکریٹ کا حساب لگائیں");
    const sendBtn = page.locator("button:has(svg.lucide-send)").first();
    await sendBtn.click();

    const renderer = page.locator("[data-testid='message-content-renderer']").first();
    await expect(renderer).toBeVisible({ timeout: 12000 });
    await expect(renderer).toHaveAttribute("dir", "rtl");

    await page.waitForTimeout(600);
    const screenshotPath = path.join(ARTIFACT_SCREENSHOT_DIR, "Phase02C-Urdu-RTL-Report.png");
    await page.screenshot({ path: screenshotPath });
    console.log(`[Screenshot Evidence] Saved: ${screenshotPath}`);

    // Reset language back to English
    await page.evaluate(() => {
      localStorage.setItem("tameerai-lang", "en");
    });
  });
});
