import { test, expect } from '@playwright/test';

test.describe('LYSTRA Chat Core UX', () => {

  test('FE-83: No-Refresh Test (Mandatory)', async ({ page }) => {
    // 1. Initial navigation
    await page.goto('/chat');

    let pageReloadCount = 0;
    page.on('framenavigated', (frame) => {
      if (frame === page.mainFrame()) {
        pageReloadCount++;
      }
    });

    // Reset counter after initial load
    pageReloadCount = 0;

    // 2. Open chat (ensure it's interactive)
    const composer = page.getByPlaceholder('Ask LYSTRA anything...');
    await expect(composer).toBeVisible();

    // 3. Send message
    await composer.fill('Hello LYSTRA! This is a test.');
    await page.click('button:has(svg.lucide-arrow-up)');

    // 4. Assistant appears, streaming starts
    const typingIndicator = page.locator('.lystra-typing-indicator, .lucide-sparkles').first();
    await expect(typingIndicator).toBeVisible({ timeout: 5000 });

    // 5. Final message visible
    const assistantMessage = page.locator('.prose').last();
    await expect(assistantMessage).toBeVisible({ timeout: 15000 });

    // 6. Assert reload count = 0
    expect(pageReloadCount).toBe(0);
  });

  test('FE-90: Chat UX Final Pass - immediate optimistic UI', async ({ page }) => {
    await page.goto('/chat');
    const composer = page.getByPlaceholder('Ask LYSTRA anything...');
    
    // Type and send
    await composer.fill('UX Test Message');
    await composer.press('Enter');

    // Immediately user message should be visible (optimistic)
    const userMessage = page.getByText('UX Test Message').first();
    await expect(userMessage).toBeVisible();

    // Wait for the stream to finish and actions to appear
    await expect(page.locator('.lucide-copy').first()).toBeVisible({ timeout: 15000 });
  });

});
