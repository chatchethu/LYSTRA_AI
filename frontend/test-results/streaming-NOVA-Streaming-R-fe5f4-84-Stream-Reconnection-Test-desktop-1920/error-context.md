# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: streaming.spec.ts >> LYSTRA Streaming Resilience >> FE-84: Stream Reconnection Test
- Location: e2e\streaming.spec.ts:40:7

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: expect(locator).toBeVisible() failed

Locator: getByText('First part. Second part.')
Expected: visible
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for getByText('First part. Second part.')
  - Test timeout of 30000ms exceeded.

```

```yaml
- img
- text: Connection Lost
- img
- text: Reconnecting...
- complementary:
  - img
  - text: LYSTRA AI
  - button "New Chat Ctrl+N":
    - img
    - text: New Chat Ctrl+N
  - img
  - paragraph: Sign in to save and view your chat history
  - link "LYSTRA Brain":
    - /url: /brain
    - img
    - text: LYSTRA Brain
  - link "Metrics":
    - /url: /metrics
    - img
    - text: Metrics
  - link "Settings":
    - /url: /settings
    - img
    - text: Settings
  - button "Sign In":
    - img
    - text: Sign In
- main:
  - img
  - text: LYSTRA Thinking... Powered by LYSTRA Reconnect test
  - img
  - text: Thinking...
  - button "Add attachment":
    - img
  - textbox "Ask LYSTRA anything..."
  - button "Voice input":
    - img
  - button "Stop generating":
    - img
  - text: LYSTRA AI can make mistakes. Verify critical information.
- alert
```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test';
  2   | import { Readable } from 'stream';
  3   | 
  4   | test.describe('LYSTRA Streaming Resilience', () => {
  5   | 
  6   |   test('FE-82: Fragmented SSE Data Reconstruction', async ({ page }) => {
  7   |     await page.route('**/api/v1/messages', async route => {
  8   |       const stream = new Readable({ read() {} });
  9   |       
  10  |       route.fulfill({
  11  |         status: 200,
  12  |         headers: { 'Content-Type': 'text/event-stream' },
  13  |         body: stream
  14  |       });
  15  | 
  16  |       // Send start event
  17  |       setTimeout(() => stream.push('data: {"event":"run.started","payload":{}}\n\n'), 50);
  18  | 
  19  |       // Simulate a split JSON payload across multiple network chunks
  20  |       setTimeout(() => stream.push('data: {"event":"message.del'), 100);
  21  |       setTimeout(() => stream.push('ta","payload":{"text":"Hel"}}\n\n'), 200);
  22  |       
  23  |       // Send the rest
  24  |       setTimeout(() => stream.push('data: {"event":"message.delta","payload":{"text":"lo"}}\n\n'), 300);
  25  |       setTimeout(() => {
  26  |         stream.push('data: {"event":"run.completed","payload":{}}\n\n');
  27  |         stream.push(null);
  28  |       }, 400);
  29  |     });
  30  | 
  31  |     await page.goto('/chat');
  32  |     await page.getByPlaceholder('Ask LYSTRA anything...').fill('Fragment test');
  33  |     await page.getByPlaceholder('Ask LYSTRA anything...').press('Enter');
  34  | 
  35  |     // UI should successfully reconstruct "Hello" without missing text
  36  |     const msg = page.getByText('Hello');
  37  |     await expect(msg).toBeVisible();
  38  |   });
  39  | 
  40  |   test('FE-84: Stream Reconnection Test', async ({ page }) => {
  41  |     let requestCount = 0;
  42  |     
  43  |     await page.route('**/api/v1/messages', async route => {
  44  |       requestCount++;
  45  |       const stream = new Readable({ read() {} });
  46  |       
  47  |       route.fulfill({
  48  |         status: 200,
  49  |         headers: { 'Content-Type': 'text/event-stream' },
  50  |         body: stream
  51  |       });
  52  | 
  53  |       stream.push('data: {"event":"run.started","payload":{}}\n\n');
  54  |       
  55  |       if (requestCount === 1) {
  56  |         stream.push('data: {"event":"message.delta","payload":{"text":"First part."}}\n\n');
  57  |         // Abruptly close the stream with an error
  58  |         setTimeout(() => stream.destroy(new Error("Network drop")), 100);
  59  |       } else {
  60  |         // Upon reconnection, replay the missing part
  61  |         stream.push('data: {"event":"message.delta","payload":{"text":" Second part."}}\n\n');
  62  |         stream.push('data: {"event":"run.completed","payload":{}}\n\n');
  63  |         setTimeout(() => stream.push(null), 50);
  64  |       }
  65  |     });
  66  | 
  67  |     await page.goto('/chat');
  68  |     await page.getByPlaceholder('Ask LYSTRA anything...').fill('Reconnect test');
  69  |     await page.getByPlaceholder('Ask LYSTRA anything...').press('Enter');
  70  | 
  71  |     // Wait for the full reconstructed message
  72  |     const msg = page.getByText('First part. Second part.');
> 73  |     await expect(msg).toBeVisible();
      |                       ^ Error: expect(locator).toBeVisible() failed
  74  |   });
  75  | 
  76  |   test('FE-85: Response Reconciliation Test', async ({ page }) => {
  77  |     await page.route('**/api/v1/messages', async route => {
  78  |       const stream = new Readable({ read() {} });
  79  |       route.fulfill({
  80  |         status: 200,
  81  |         headers: { 'Content-Type': 'text/event-stream' },
  82  |         body: stream
  83  |       });
  84  | 
  85  |       stream.push('data: {"event":"run.started","payload":{}}\n\n');
  86  |       // The backend echoes the user message as 'message.accepted'
  87  |       stream.push('data: {"event":"message.accepted","payload":{"message":"Reconciliation check"}}\n\n');
  88  |       stream.push('data: {"event":"message.delta","payload":{"text":"Assistant replied"}}\n\n');
  89  |       stream.push('data: {"event":"run.completed","payload":{}}\n\n');
  90  |       stream.push(null);
  91  |     });
  92  | 
  93  |     await page.goto('/chat');
  94  |     await page.getByPlaceholder('Ask LYSTRA anything...').fill('Reconciliation check');
  95  |     await page.getByPlaceholder('Ask LYSTRA anything...').press('Enter');
  96  | 
  97  |     // Expected: 1 User message, 1 Assistant message (no duplicates)
  98  |     await expect(page.getByText('Reconciliation check')).toHaveCount(1);
  99  |     await expect(page.getByText('Assistant replied')).toHaveCount(1);
  100 |   });
  101 | 
  102 |   test('FE-86: Long Response Scroll Stability', async ({ page }) => {
  103 |     await page.route('**/api/v1/messages', async route => {
  104 |       const stream = new Readable({ read() {} });
  105 |       route.fulfill({
  106 |         status: 200,
  107 |         headers: { 'Content-Type': 'text/event-stream' },
  108 |         body: stream
  109 |       });
  110 | 
  111 |       stream.push('data: {"event":"run.started","payload":{}}\n\n');
  112 |       
  113 |       // Stream an enormous payload very fast
  114 |       const hugeMarkdown = Array(100).fill('Here is a large block of text designed to test virtualization and scrolling stability.\n\n```python\nprint("Hello World")\n```\n\n').join('');
  115 |       
  116 |       let index = 0;
  117 |       const interval = setInterval(() => {
  118 |         if (index >= hugeMarkdown.length) {
  119 |           clearInterval(interval);
  120 |           stream.push('data: {"event":"run.completed","payload":{}}\n\n');
  121 |           stream.push(null);
  122 |           return;
  123 |         }
  124 |         const chunk = hugeMarkdown.slice(index, index + 500);
  125 |         stream.push(`data: {"event":"message.delta","payload":{"text":${JSON.stringify(chunk)}}}\n\n`);
  126 |         index += 500;
  127 |       }, 5);
  128 |     });
  129 | 
  130 |     await page.goto('/chat');
  131 |     await page.getByPlaceholder('Ask LYSTRA anything...').fill('Long string');
  132 |     await page.getByPlaceholder('Ask LYSTRA anything...').press('Enter');
  133 | 
  134 |     // Assert that the page does not freeze and the final block renders
  135 |     await expect(page.locator('.prose')).toBeVisible();
  136 |     await expect(page.locator('.prose')).toContainText('Hello World', { timeout: 15000 });
  137 |   });
  138 | });
  139 | 
```