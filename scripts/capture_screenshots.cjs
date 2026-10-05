/* Optional development tool: run against a local, seeded Django server. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {
  chromium
} = require('playwright');

const root = path.resolve(__dirname, '..');
const output = path.join(root, 'screenshots');
const baseURL = process.env.APP_URL || 'http://127.0.0.1:8000';
if (!['127.0.0.1', 'localhost', '[::1]'].includes(new URL(baseURL).hostname)) {
  throw new Error('Screenshot automation is restricted to a local demo server.');
}
fs.mkdirSync(output, {
  recursive: true
});

(async () => {
  const browser = await chromium.launch({
    headless: true,
    ...(process.env.BROWSER_EXECUTABLE ? {
      executablePath: process.env.BROWSER_EXECUTABLE
    } : {})
  });
  const context = await browser.newContext({
    viewport: {
      width: 1440,
      height: 1000
    },
    deviceScaleFactor: 1,
    colorScheme: 'light',
    reducedMotion: 'reduce'
  });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  page.on('response', (response) => {
    if (response.status() >= 400 && !response.url().endsWith('.map')) {
      errors.push(`${response.status()} ${response.url()}`);
    }
  });
  const visit = async (url) => {
    const response = await page.goto(`${baseURL}${url}`, {
      waitUntil: 'networkidle'
    });
    assert.equal(response.status(), 200, url);
  };
  const capture = async (name) => {
    await page.evaluate(() => {
      if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
      window.scrollTo(0, 0);
    });
    await page.screenshot({
      path: path.join(output, name),
      fullPage: true
    });
  };
  try {
    await visit('/predict/');
    await page.selectOption('#id_location', 'Riverside');
    await page.selectOption('#id_property_type', 'Detached');
    await page.selectOption('#id_furnishing_status', 'Semi-furnished');
    for (const [name, value] of Object.entries({
        area_sqft: '1800',
        bedrooms: '3',
        bathrooms: '2',
        floors: '2',
        property_age: '8',
        parking_spaces: '1',
        distance_city_center: '5.5'
      })) {
      await page.fill(`#id_${name}`, value);
    }
    await page.check('#id_nearby_school');
    await capture('prediction-page.png');
    // Native browser constraints must reject impossible values before submission.
    await page.fill('#id_area_sqft', '-1');
    assert.equal(await page.locator('#predictionForm').evaluate((form) => form.checkValidity()), false);
    await page.fill('#id_area_sqft', '1800');
    await Promise.all([
      page.waitForURL('**/result/**'),
      page.click('#predictButton'),
    ]);
    assert.match(await page.locator('.result-price').innerText(), /\$[\d,]+/);
    await capture('result-page.png');
    await visit('/history/');
    assert.ok(await page.locator('.history-table tbody tr').count() >= 1);
    await capture('history-page.png');
    await visit('/');
    assert.equal(await page.locator('#locationChart').evaluate(() => Chart.getChart('locationChart').data.labels.length > 0), true);
    assert.equal(await page.locator('#chartTableBody tr').count(), 6);
    await capture('home-page.png');
    await visit('/about/');
    assert.ok(await page.locator('.comparison-panel tbody tr').count() === 3);
    await capture('about-page.png');
    await visit('/admin/login/');
    await page.fill('#id_username', 'admin');
    await page.fill('#id_password', 'Admin@12345');
    await Promise.all([page.waitForURL('**/admin/'), page.click('input[type="submit"]')]);
    assert.match(await page.locator('#site-name').innerText(), /House Price Prediction Administration/);
    await capture('admin-dashboard.png');
    // Test navigation and horizontal overflow at mobile and tablet widths.
    for (const width of [375, 768]) {
      await page.setViewportSize({
        width,
        height: 900
      });
      for (const url of ['/', '/predict/', '/history/', '/about/']) {
        await visit(url);
        const dimensions = await page.evaluate(() => ({
          viewport: document.documentElement.clientWidth,
          content: document.documentElement.scrollWidth,
        }));
        assert.ok(dimensions.content <= dimensions.viewport + 1,
          `${url} overflows at ${width}px: ${JSON.stringify(dimensions)}`);
        if (width === 375 && url === '/') {
          await capture('mobile-home.png');
          await page.click('.navbar-toggler');
          assert.equal(await page.locator('#mainNav').isVisible(), true);
          await page.locator('#mainNav').getByRole('link', {
            name: 'Predict',
            exact: true
          }).click();
          await page.waitForURL('**/predict/');
        }
        if (width === 375 && url === '/predict/') await capture('mobile-prediction.png');
      }
    }
    assert.deepEqual(errors, [], 'Browser JavaScript or HTTP errors');
    console.log('Browser checks passed: prediction, result, history, chart, about, admin, and 375/768px layouts.');
    console.log(`Screenshots saved in ${output}`);
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
