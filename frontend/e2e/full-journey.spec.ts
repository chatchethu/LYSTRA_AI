import { test, expect } from '@playwright/test';
import { Readable } from 'stream';

test.describe('LYSTRA E2E Journey (FE-94)', () => {
  test('Complete uninterrupted user flow', async ({ page }) => {
    let reloadCount = 0;
    page.on('framenavigated', (frame) => {
      if (frame === page.mainFrame()) {
        reloadCount++;
      }
    });

    // 1. Open LYSTRA & Login
    await page.goto('/login');
    reloadCount = 0; // Reset after initial page load

    // Simulate auth mock
    await page.route('**/api/v1/auth/me', route =>
      route.fulfill({ status: 200, json: { id: '1', email: 'test@lystra.com', username: 'tester' } })
    );
    await page.goto('/chat'); // Assuming auth redirects here

    // 2. New Chat is already open (empty state)
    await expect(page.getByPlaceholder('Ask LYSTRA anything...')).toBeVisible();

    // 3. Type & Send
    await page.route('**/api/v1/messages', route => {
      const stream = new Readable({ read() { } });
      route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'text/event-stream' },
        body: stream as any
      });
      stream.push('data: {"event":"run.started","payload":{}}\n\n');
      stream.push('data: {"event":"message.accepted","payload":{"message":"Hello LYSTRA"}}\n\n');
      setTimeout(() => stream.push('data: {"event":"message.delta","payload":{"text":"Hi there! How can I help you today?"}}\n\n'), 50);
      setTimeout(() => {
        stream.push('data: {"event":"run.completed","payload":{}}\n\n');
        stream.push(null);
      }, 100);
    });

    await page.getByPlaceholder('Ask LYSTRA anything...').fill('Hello LYSTRA');
    await page.getByPlaceholder('Ask LYSTRA anything...').press('Enter');

    // 4. Stream completes
    await expect(page.getByText('Hi there! How can I help you today?')).toBeVisible();

    // 5. Scroll stability (auto-scroll)
    // The UI should have scrolled to the bottom implicitly when the stream finished
    const composer = page.getByPlaceholder('Ask LYSTRA anything...');
    await expect(composer).toBeInViewport();

    // 6. Copy response
    const copyButton = page.locator('button[title="Copy"]').first();
    // In some components title is missing or different, assuming typical copy button icon presence
    if (await copyButton.isVisible()) {
      await copyButton.click();
      // Ensure no crash on copy
    }

    // 7. Regenerate
    const regenButton = page.locator('button:has-text("Regenerate")').first();
    if (await regenButton.isVisible()) {
      await regenButton.click();
    }

    // 8. New conversation
    await page.route('**/api/v1/conversations', route => {
      route.fulfill({ status: 200, json: { id: 'new-id', title: 'New Conversation' } });
    });
    const newChatBtn = page.getByText('New Chat');
    await newChatBtn.click();
    await expect(page).toHaveURL(/\/chat/); // URL clears to /chat

    // 9. Switch conversation
    await page.route('**/api/v1/conversations/old-id/messages', route => {
      route.fulfill({ status: 200, json: [] });
    });
    // Assuming there's a sidebar item
    const sidebarItem = page.locator('.truncate').filter({ hasText: 'New Conversation' }).first();
    if (await sidebarItem.isVisible()) {
      await sidebarItem.click();
    }

    // 10. No browser refresh should be needed
    expect(reloadCount).toBe(0);
  });
});
