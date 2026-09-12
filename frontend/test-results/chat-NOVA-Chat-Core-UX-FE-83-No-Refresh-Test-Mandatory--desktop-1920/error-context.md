# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: chat.spec.ts >> LYSTRA Chat Core UX >> FE-83: No-Refresh Test (Mandatory)
- Location: e2e\chat.spec.ts:5:7

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: page.click: Test timeout of 30000ms exceeded.
Call log:
  - waiting for locator('button:has(svg.lucide-arrow-up)')

```

# Page snapshot

```yaml
- generic [ref=e1]:
  - generic [ref=e2]:
    - generic [ref=e3]:
      - generic [ref=e11]: Connection Lost
      - generic [ref=e12]: Reconnecting...
    - complementary [ref=e19]:
      - generic [ref=e20]: LYSTRA AI
      - button "New Chat Ctrl+N" [ref=e34] [cursor=pointer]:
        - text: New Chat
        - generic [ref=e36]: Ctrl+N
      - paragraph [ref=e41]: Sign in to save and view your chat history
      - generic [ref=e42]:
        - link "LYSTRA Brain" [ref=e43] [cursor=pointer]:
          - /url: /brain
        - link "Metrics" [ref=e56] [cursor=pointer]:
          - /url: /metrics
        - link "Settings" [ref=e59] [cursor=pointer]:
          - /url: /settings
      - button "Sign In" [ref=e64] [cursor=pointer]
    - main [ref=e68]:
      - generic [ref=e69]:
        - generic [ref=e70]:
          - generic [ref=e83]:
            - generic [ref=e84]: LYSTRA
            - generic [ref=e86]: Ready
          - generic [ref=e88]: Powered by LYSTRA
        - generic [ref=e90]:
          - heading "Good morning." [level=1] [ref=e94]
          - paragraph [ref=e95]: What are you working on?
          - generic [ref=e96]:
            - button "Plan something Create a schedule or project plan" [ref=e97] [cursor=pointer]:
              - generic [ref=e98]: Plan something
              - generic [ref=e99]: Create a schedule or project plan
            - button "Brainstorm an idea Generate creative concepts" [ref=e100] [cursor=pointer]:
              - generic [ref=e101]: Brainstorm an idea
              - generic [ref=e102]: Generate creative concepts
            - button "Solve a problem Debug code or analyze logic" [ref=e103] [cursor=pointer]:
              - generic [ref=e104]: Solve a problem
              - generic [ref=e105]: Debug code or analyze logic
            - button "Talk with me Have a casual conversation" [ref=e106] [cursor=pointer]:
              - generic [ref=e107]: Talk with me
              - generic [ref=e108]: Have a casual conversation
        - generic [ref=e110]:
          - generic [ref=e112]:
            - button "Add attachment" [ref=e113] [cursor=pointer]
            - textbox "Ask LYSTRA anything..." [active] [ref=e115]: Hello LYSTRA! This is a test.
            - generic [ref=e116]:
              - button "Voice input" [ref=e117] [cursor=pointer]
              - button "Send message" [ref=e121] [cursor=pointer]
          - generic [ref=e125]: LYSTRA AI can make mistakes. Verify critical information.
  - button "Open Next.js Dev Tools" [ref=e131] [cursor=pointer]
  - alert [ref=e135]
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
> 25 |     await page.click('button:has(svg.lucide-arrow-up)');
     |                ^ Error: page.click: Test timeout of 30000ms exceeded.
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
  40 |     await page.goto('/chat');
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