import { test, expect } from "@playwright/test";

test.describe("Client-Side Route Navigation", () => {
  test("navigates directly to /subscriptions and renders subscriptions table", async ({
    page,
  }) => {
    await page.goto("/subscriptions");
    await expect(page).toHaveURL(/.*\/subscriptions/);
    await expect(page.locator("h1")).toContainText(/Subscriptions|Subscription/i);
    // Table or list container should be present
    await expect(page.locator("table, [role='table']")).toBeVisible({
      timeout: 10000,
    });
  });

  test("navigates directly to /findings and renders waste finder review cards", async ({
    page,
  }) => {
    await page.goto("/findings");
    await expect(page).toHaveURL(/.*\/findings/);
    await expect(page.locator("h1, h2")).toContainText(/Waste Finder|Findings/i);
  });

  test("navigates directly to /connections and renders data connections management", async ({
    page,
  }) => {
    await page.goto("/connections");
    await expect(page).toHaveURL(/.*\/connections/);
    await expect(page.locator("h1, h2")).toContainText(/Connections|Integrations/i);
  });

  test("verifies seamless in-app client-side navigation across all primary routes", async ({
    page,
  }) => {
    // 1. Start at home / overview
    await page.goto("/");
    await expect(page).toHaveURL(/.*\/$/);
    await expect(page.locator("body")).toBeVisible();

    // 2. Click Subscriptions link
    const subsLink = page.locator("a[href='/subscriptions']").first();
    await expect(subsLink).toBeVisible({ timeout: 10000 });
    await subsLink.click();
    await expect(page).toHaveURL(/.*\/subscriptions/);
    await expect(page.locator("h1")).toContainText(/Subscriptions/i);

    // 3. Click Waste Finder link
    const findingsLink = page.locator("a[href='/findings']").first();
    await expect(findingsLink).toBeVisible();
    await findingsLink.click();
    await expect(page).toHaveURL(/.*\/findings/);

    // 4. Click Connections link
    const connLink = page.locator("a[href='/integrations'], a[href='/connections']").first();
    await expect(connLink).toBeVisible();
    await connLink.click();
    await expect(page).toHaveURL(/.*\/(integrations|connections)/);

    // 5. Navigate to Collaborative Session
    const sessionLink = page.locator("a[href='/session']").first();
    if (await sessionLink.isVisible()) {
      await sessionLink.click();
      await expect(page).toHaveURL(/.*\/session/);
      await expect(page.locator('[data-testid="session-page"]')).toBeVisible();
    }
  });
});
