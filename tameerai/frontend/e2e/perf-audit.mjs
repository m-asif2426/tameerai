import { chromium } from "playwright";

async function measurePage(url, name) {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  const start = Date.now();
  await page.goto(url, { waitUntil: "networkidle" });
  const loadTime = Date.now() - start;

  const performanceMetrics = await page.evaluate(() => {
    const nav = performance.getEntriesByType("navigation")[0];
    return {
      ttfb: Math.round(nav.responseStart - nav.requestStart),
      domContentLoaded: Math.round(nav.domContentLoadedEventEnd - nav.startTime),
      loadDuration: Math.round(nav.loadEventEnd - nav.startTime),
      transferSize: nav.transferSize,
      decodedBodySize: nav.decodedBodySize
    };
  });

  const a11yMetrics = await page.evaluate(() => {
    const images = Array.from(document.querySelectorAll("img"));
    const imagesMissingAlt = images.filter(img => !img.hasAttribute("alt") || img.getAttribute("alt") === "");
    
    const inputs = Array.from(document.querySelectorAll("input, select, textarea"));
    const inputsWithoutLabels = inputs.filter(inp => {
      const id = inp.getAttribute("id");
      const hasAriaLabel = inp.hasAttribute("aria-label") || inp.hasAttribute("aria-labelledby");
      const hasAssociatedLabel = id ? !!document.querySelector(`label[for="${id}"]`) : false;
      const isWrapped = !!inp.closest("label");
      return !hasAriaLabel && !hasAssociatedLabel && !isWrapped;
    });

    const headings = Array.from(document.querySelectorAll("h1, h2, h3, h4, h5, h6")).map(h => ({
      level: parseInt(h.tagName[1]),
      text: h.textContent.trim().slice(0, 30)
    }));

    const ariaLandmarks = Array.from(document.querySelectorAll("header, nav, main, aside, footer, [role]")).map(el => 
      el.tagName.toLowerCase() + (el.getAttribute("role") ? `[role=${el.getAttribute("role")}]` : "")
    );

    return {
      totalImages: images.length,
      imagesMissingAlt: imagesMissingAlt.length,
      totalInputs: inputs.length,
      inputsWithoutLabels: inputsWithoutLabels.length,
      headingsCount: headings.length,
      ariaLandmarksCount: ariaLandmarks.length
    };
  });

  await browser.close();
  return { name, url, loadTime, performanceMetrics, a11yMetrics };
}

async function run() {
  console.log("=== MEASURING PERFORMANCE & ACCESSIBILITY ===");
  const results = [];
  const pages = [
    { name: "Public Homepage", url: "http://localhost:3000/" },
    { name: "Login Portal", url: "http://localhost:3000/login" },
    { name: "Signup Portal", url: "http://localhost:3000/signup" }
  ];

  for (const p of pages) {
    const res = await measurePage(p.url, p.name);
    results.push(res);
    console.log(`\n[${res.name}] (${res.url}):`);
    console.log(`  Load Time: ${res.loadTime} ms`);
    console.log(`  TTFB: ${res.performanceMetrics.ttfb} ms`);
    console.log(`  DOMContentLoaded: ${res.performanceMetrics.domContentLoaded} ms`);
    console.log(`  Total Transfer: ${(res.performanceMetrics.transferSize / 1024).toFixed(1)} KB`);
    console.log(`  A11y: ${res.a11yMetrics.imagesMissingAlt} missing alt / ${res.a11yMetrics.totalImages} images`);
    console.log(`  A11y: ${res.a11yMetrics.inputsWithoutLabels} unlabelled / ${res.a11yMetrics.totalInputs} inputs`);
    console.log(`  A11y: ${res.a11yMetrics.headingsCount} headings, ${res.a11yMetrics.ariaLandmarksCount} semantic landmarks`);
  }
}

run().catch(console.error);

