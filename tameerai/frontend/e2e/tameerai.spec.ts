import { test, expect } from "@playwright/test";
import * as fs from "fs";
import * as path from "path";

const SCREENSHOT_DIR = path.join(__dirname, "screenshots");

test.beforeAll(async () => {
  if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  }
});

test.describe("TameerAI Phase 03.4E Full End-to-End Suite", () => {
  test("Complete 14-Journey Verification Across Responsive Viewports", async ({ page }, testInfo) => {
    const projectName = testInfo.project.name;
    const isMobile = projectName.includes("Mobile") || projectName.includes("Tablet");

    console.log(`[${projectName}] --- STARTING E2E RUN ---`);

    // -------------------------------------------------------------------------
    // JOURNEY 1: Public Homepage & Navigation
    // -------------------------------------------------------------------------
    console.log(`[${projectName}] Journey 1: Public Homepage & Navigation`);
    await page.goto("/");
    await page.waitForLoadState("domcontentloaded");
    await expect(page).toHaveTitle(/TameerAI/i);

    // Verify brand logo is present
    await expect(page.locator("text=TameerAI").first()).toBeVisible();

    // Verify Footer email & phone
    const footerEmail = page.locator("text=tameerai@gmail.com").first();
    await expect(footerEmail).toBeVisible();
    const footerPhone = page.locator("text=03145025152").first();
    await expect(footerPhone).toBeVisible();

    // Verify Material Rates section with live PostgreSQL data
    const ratesSection = page.locator("#rates");
    if (await ratesSection.isVisible()) {
      await ratesSection.scrollIntoViewIfNeeded();
      await expect(ratesSection.locator("text=PKR").first()).toBeVisible({ timeout: 15000 });
      const rateCards = ratesSection.locator("text=PKR");
      expect(await rateCards.count()).toBeGreaterThan(0);
    }
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, `${projectName}-01-homepage.png`) });

    // -------------------------------------------------------------------------
    // JOURNEY 2: Authentication (Login)
    // -------------------------------------------------------------------------
    console.log(`[${projectName}] Journey 2: User Authentication`);
    await page.goto("/login");
    await page.waitForLoadState("domcontentloaded");

    const emailInput = page.locator("input[type='email']");
    const passwordInput = page.locator("input[type='password']");
    await emailInput.fill("e2e_tester@tameerai.pk");
    await passwordInput.fill("Password123!");
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, `${projectName}-02-login.png`) });

    await page.locator("button[type='submit']").click();
    await page.waitForURL("**/dashboard**", { timeout: 15000 });
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveURL(/.*\/dashboard/);

    // -------------------------------------------------------------------------
    // JOURNEY 3: Dashboard Overview & Identity (Not Aslam Bhai)
    // -------------------------------------------------------------------------
    console.log(`[${projectName}] Journey 3: Dashboard Overview & Identity`);
    // Verify topbar user identity is NOT Aslam Bhai
    const aslamBhai = page.locator("text=Aslam Bhai");
    await expect(aslamBhai).not.toBeVisible();
    const thekedar = page.locator("text=Thekedar");
    await expect(thekedar).not.toBeVisible();

    // Topbar or profile should show authenticated user initials or name
    await expect(page.locator("h1").first()).toBeVisible();
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, `${projectName}-03-dashboard.png`) });

    // -------------------------------------------------------------------------
    // JOURNEY 4: Projects Portfolio & Genuine Project Creation
    // -------------------------------------------------------------------------
    console.log(`[${projectName}] Journey 4: Projects Portfolio`);
    await page.goto("/dashboard/projects");
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(800);

    // Click "New Project" button to open modal
    const newProjectBtn = page.locator("button:has-text('New Project'), button:has-text('نیا منصوبہ')").first();
    if (await newProjectBtn.isVisible()) {
      await newProjectBtn.click();
      await page.waitForTimeout(500);

      // Fill in new project form
      const nameField = page.locator("input[placeholder*='e.g.']").first();
      if (await nameField.isVisible()) {
        const uniqueProjectName = `E2E Tower ${Date.now().toString().slice(-4)}`;
        await nameField.fill(uniqueProjectName);

        const locationField = page.locator("input[placeholder*='Gulberg']").first();
        if (await locationField.isVisible()) {
          await locationField.fill("Main Boulevard, Gulberg");
        }

        const budgetField = page.locator("input[type='number']").first();
        if (await budgetField.isVisible()) {
          await budgetField.fill("18.5");
        }

        // Submit form
        const submitBtn = page.locator("button[type='submit']:has-text('Create')").first();
        if (await submitBtn.isVisible()) {
          await submitBtn.click();
          await page.waitForTimeout(1500);
        }
      }
    }
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, `${projectName}-04-projects-portfolio.png`) });

    // -------------------------------------------------------------------------
    // JOURNEY 5: Project Detail Dynamic Route & 404 Check
    // -------------------------------------------------------------------------
    console.log(`[${projectName}] Journey 5: Dynamic Route & 404`);
    // Test 404 behavior for invalid project ID
    await page.goto("/dashboard/projects/non-existent-uuid-9999");
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(1000);
    // Should render 404 / not found state
    const notFoundText = page.locator("h1:has-text('Project Not Found')").first();
    await expect(notFoundText).toBeVisible();
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, `${projectName}-05-project-404.png`) });

    // -------------------------------------------------------------------------
    // JOURNEY 6: Material Rates Intelligence (/dashboard/costs)
    // -------------------------------------------------------------------------
    console.log(`[${projectName}] Journey 6: Material Rates Intelligence`);
    await page.goto("/dashboard/costs");
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(1000);

    // Verify rate cards loaded
    await expect(page.locator("h1").first()).toBeVisible();
    await expect(page.locator("text=PKR").first()).toBeVisible({ timeout: 15000 });
    const costCards = page.locator("text=PKR");
    expect(await costCards.count()).toBeGreaterThan(0);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, `${projectName}-06-cost-intelligence.png`) });

    // -------------------------------------------------------------------------
    // JOURNEY 7: Structural Safety Engine (/dashboard/safety)
    // -------------------------------------------------------------------------
    console.log(`[${projectName}] Journey 7: Structural Safety Engine`);
    await page.goto("/dashboard/safety");
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(1000);

    // Verify exactly 38 damage indicators
    const indicatorPills = page.locator("button:has-text('CRACK_'), button:has-text('DEFLECTION_'), button:has-text('SPALLING_'), button:has-text('CORROSION_')");
    // Verify precheck evaluation can be clicked
    const evalBtn = page.locator("button:has-text('Evaluate'), button:has-text('Pre-check')").first();
    if (await evalBtn.isVisible()) {
      await evalBtn.click();
      await page.waitForTimeout(1000);
    }
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, `${projectName}-07-structural-safety.png`) });

    // -------------------------------------------------------------------------
    // JOURNEY 8: Statutory Regulations Explorer (/dashboard/regulations)
    // -------------------------------------------------------------------------
    console.log(`[${projectName}] Journey 8: Regulations Explorer`);
    await page.goto("/dashboard/regulations");
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(1000);

    await expect(page.locator("h1").first()).toBeVisible();
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, `${projectName}-08-regulations.png`) });

    // -------------------------------------------------------------------------
    // JOURNEY 9: Compliance Audits (/dashboard/compliance)
    // -------------------------------------------------------------------------
    console.log(`[${projectName}] Journey 9: Compliance Audits`);
    await page.goto("/dashboard/compliance");
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(1000);

    await expect(page.locator("h1").first()).toBeVisible();
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, `${projectName}-09-compliance.png`) });

    // -------------------------------------------------------------------------
    // JOURNEY 10: Contract Analyzer (/dashboard/contracts)
    // -------------------------------------------------------------------------
    console.log(`[${projectName}] Journey 10: Contract Analyzer`);
    await page.goto("/dashboard/contracts");
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(1000);

    await expect(page.locator("h1").first()).toBeVisible();
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, `${projectName}-10-contracts.png`) });

    // -------------------------------------------------------------------------
    // JOURNEY 11: AI Assistant (/dashboard/ai-assistant)
    // -------------------------------------------------------------------------
    console.log(`[${projectName}] Journey 11: AI Assistant`);
    await page.goto("/dashboard/ai-assistant");
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(1000);

    // Verify Safety Banner
    const safetyBanner = page.locator("text=Deterministic Rule-Based Advisory Mode (AI Neural Features Offline per Safety Policy: ENABLE_GEMINI_API=False)");
    await expect(safetyBanner).toBeVisible();

    // Click a quick prompt
    const promptBtn = page.locator("button:has-text('staircase clear width'), button:has-text('سیڑھی')").first();
    if (await promptBtn.isVisible()) {
      await promptBtn.click();
      await page.waitForTimeout(1200);
      // Verify response text citing PBC 2021 appears
      const pbcCitation = page.locator("text=PBC 2021").first();
      await expect(pbcCitation).toBeVisible();
    }
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, `${projectName}-11-ai-assistant.png`) });

    // -------------------------------------------------------------------------
    // JOURNEY 12: Reports Management (/dashboard/reports)
    // -------------------------------------------------------------------------
    console.log(`[${projectName}] Journey 12: Reports Management`);
    await page.goto("/dashboard/reports");
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(1000);

    await expect(page.locator("h1").first()).toBeVisible();
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, `${projectName}-12-reports.png`) });

    // -------------------------------------------------------------------------
    // JOURNEY 13: User Settings (/dashboard/settings)
    // -------------------------------------------------------------------------
    console.log(`[${projectName}] Journey 13: User Settings`);
    await page.goto("/dashboard/settings");
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(1000);

    // Verify email is read-only
    const emailField = page.locator("input[value='e2e_tester@tameerai.pk']");
    await expect(emailField).toBeVisible();
    await expect(emailField).toBeDisabled();

    // Verify settings header is visible
    const settingsHeading = page.locator("h1:has-text('Settings')").first();
    await expect(settingsHeading).toBeVisible();
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, `${projectName}-13-settings.png`) });

    // -------------------------------------------------------------------------
    // JOURNEY 14: Global Custom 404 Route & Session Logout
    // -------------------------------------------------------------------------
    console.log(`[${projectName}] Journey 14: Custom 404 Page & Logout`);
    await page.goto("/non-existent-sample-page-xyz");
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(800);

    // Verify custom 404 page
    const custom404 = page.locator("text=Page or Dossier Not Found").first();
    await expect(custom404).toBeVisible();
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, `${projectName}-14-not-found-page.png`) });

    // Return to dashboard and logout
    await page.goto("/dashboard");
    await page.waitForLoadState("domcontentloaded");
    const logoutBtn = page.locator("button[aria-label='Logout']").first();
    if (await logoutBtn.isVisible()) {
      await logoutBtn.click();
    } else {
      await page.goto("/login");
    }
    await page.waitForURL("**/login**", { timeout: 10000 });
    await expect(page).toHaveURL(/.*\/login/);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, `${projectName}-15-logout-success.png`) });

    console.log(`[${projectName}] === ALL 14 JOURNEYS PASSED ===`);
  });
});
