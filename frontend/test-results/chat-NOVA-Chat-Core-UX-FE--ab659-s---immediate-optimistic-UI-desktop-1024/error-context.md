# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: chat.spec.ts >> LYSTRA Chat Core UX >> FE-90: Chat UX Final Pass - immediate optimistic UI
- Location: e2e\chat.spec.ts:39:7

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/chat
Call log:
  - navigating to "http://localhost:3000/chat", waiting until "load"

```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test.describe('LYSTRA Chat Core UX', () => {
  4  | 
  5  |   test('FE-83: No-Refresh Test (Mandatory)', async ({ page }) => {
  6  |     // 1. Initial navigation
  7  |     await page.goto('/chat');
  8  | 
  9  |     let pageReloadCount = 0;
  10 |     page.on('framenavigated', (frame) => {
  11 |       if (frame === page.mainFrame()) {
  12 |         pageReloadCount++;
  13 |       }
  14 |     });
  15 | 
  16 |     // Reset counter after initial load
  17 |     pageReloadCount = 0;
  18 | 
  19 |     // 2. Open chat (ensure it's interactive)
  20 |     const composer = page.getByPlaceholder('Ask LYSTRA anything...');
  21 |     await expect(composer).toBeVisible();
  22 | 
  23 |     // 3. Send message
  24 |     await composer.fill('Hello LYSTRA! This is a test.');
  25 |     await page.click('button:has(svg.lucide-arrow-up)');
  26 | 
  27 |     // 4. Assistant appears, streaming starts
  28 |     const typingIndicator = page.locator('.lystra-typing-indicator, .lucide-sparkles').first();
  29 |     await expect(typingIndicator).toBeVisible({ timeout: 5000 });
  30 | 
  31 |     // 5. Final message visible
  32 |     const assistantMessage = page.locator('.prose').last();
  33 |     await expect(assistantMessage).toBeVisible({ timeout: 15000 });
  34 | 
  35 |     // 6. Assert reload count = 0
  36 |     expect(pageReloadCount).toBe(0);
  37 |   });
  38 | 
  39 |   test('FE-90: Chat UX Final Pass - immediate optimistic UI', async ({ page }) => {
> 40 |     await page.goto('/chat');
     |                ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/chat
  41 |     const composer = page.getByPlaceholder('Ask LYSTRA anything...');
  42 |     
  43 |     // Type and send
  44 |     await composer.fill('UX Test Message');
  45 |     await composer.press('Enter');
  46 | 
  47 |     // Immediately user message should be visible (optimistic)
  48 |     const userMessage = page.getByText('UX Test Message').first();
  49 |     await expect(userMessage).toBeVisible();
  50 | 
  51 |     // Wait for the stream to finish and actions to appear
  52 |     await expect(page.locator('.lucide-copy').first()).toBeVisible({ timeout: 15000 });
  53 |   });
  54 | 
  55 | });
  56 | 
```