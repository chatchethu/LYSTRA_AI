# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: streaming.spec.ts >> LYSTRA Streaming Resilience >> FE-86: Long Response Scroll Stability
- Location: e2e\streaming.spec.ts:102:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('.prose')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for locator('.prose')

```

```yaml
- img
- text: Connection Lost
- img
- text: Reconnecting... LYSTRA
- button "Toggle Menu":
  - img
- complementary:
  - img
  - text: LYSTRA AI
  - button "New ChatCtrl+N":
    - img
    - text: New ChatCtrl+N
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
  - text: LYSTRA Ready Powered by LYSTRA
  - img
  - heading "Good morning." [level=1]
  - paragraph: What are you working on?
  - button "Plan somethingCreate a schedule or project plan"
  - button "Brainstorm an ideaGenerate creative concepts"
  - button "Solve a problemDebug code or analyze logic"
  - button "Talk with meHave a casual conversation"
  - button "Add attachment":
    - img
  - textbox "Ask LYSTRA anything...": Long string
  - button "Voice input":
    - img
  - button "Send message" [disabled]:
    - img
  - text: LYSTRA AI can make mistakes. Verify critical information.
```

# Test source

```ts
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
  73  |     await expect(msg).toBeVisible();
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
> 135 |     await expect(page.locator('.prose')).toBeVisible();
      |                                          ^ Error: expect(locator).toBeVisible() failed
  136 |     await expect(page.locator('.prose')).toContainText('Hello World', { timeout: 15000 });
  137 |   });
  138 | });
  139 | 
```