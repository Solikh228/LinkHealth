import { test, expect } from "@playwright/test";

test.describe("Two-Session Collaboration Workflow", () => {
  test("Session 1 (interviewer) creates a room/session, Session 2 (candidate) joins via link, updates an element on the canvas/UI, and verify Session 1 sees the real-time update", async ({
    browser,
  }) => {
    // -------------------------------------------------------------------------
    // Session 1: Interviewer creates a room/session
    // -------------------------------------------------------------------------
    const interviewerContext = await browser.newContext();
    const interviewerPage = await interviewerContext.newPage();

    await interviewerPage.goto("/session");
    const createBtn = interviewerPage
      .locator('[data-testid="create-room-btn"], [data-testid="create-session-btn"]')
      .first();
    await expect(createBtn).toBeVisible({ timeout: 10000 });
    await createBtn.click();

    // Verify room is created and share link is generated
    const shareInput = interviewerPage.locator('[data-testid="share-link-input"]');
    await expect(shareInput).toBeVisible({ timeout: 10000 });
    const shareUrl = await shareInput.inputValue();
    expect(shareUrl).toContain("room=");

    // Verify initial element is rendered on Interviewer's canvas
    const interviewerElement = interviewerPage.locator('[data-testid="element-title"]');
    await expect(interviewerElement).toBeVisible();
    const initialTitle = await interviewerElement.textContent();
    expect(initialTitle).toBeTruthy();

    // -------------------------------------------------------------------------
    // Session 2: Candidate joins via the shareable link
    // -------------------------------------------------------------------------
    const candidateContext = await browser.newContext();
    const candidatePage = await candidateContext.newPage();

    await candidatePage.goto(shareUrl);

    // Verify candidate is inside the collaborative canvas room
    await expect(candidatePage.locator('[data-testid="canvas-container"]')).toBeVisible({
      timeout: 10000,
    });
    await expect(candidatePage.locator('[data-testid="canvas-element"]')).toBeVisible();

    // -------------------------------------------------------------------------
    // Candidate updates an element on the canvas/UI
    // -------------------------------------------------------------------------
    const newElementTitle = "Distributed Message Queue Cluster — Candidate Design";
    const candidateInput = candidatePage.locator('[data-testid="element-input"]');
    await candidateInput.fill(newElementTitle);
    await candidatePage.locator('[data-testid="update-element-btn"]').click();

    // Verify Candidate sees the updated element title
    await expect(candidatePage.locator('[data-testid="element-title"]')).toHaveText(
      newElementTitle
    );

    // -------------------------------------------------------------------------
    // Verify Session 1 (Interviewer) receives real-time update on their canvas
    // -------------------------------------------------------------------------
    await expect(interviewerPage.locator('[data-testid="element-title"]')).toHaveText(
      newElementTitle,
      { timeout: 10000 }
    );

    // Teardown
    await interviewerContext.close();
    await candidateContext.close();
  });
});
