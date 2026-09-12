import { test, expect } from '@playwright/test';
import { Readable } from 'stream';

test.describe('LYSTRA Streaming Resilience', () => {

  test('FE-82: Fragmented SSE Data Reconstruction', async ({ page }) => {
    await page.route('**/api/v1/messages', async route => {
      const stream = new Readable({ read() { } });

      route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'text/event-stream' },
        body: stream as any
      });

      // Send start event
      setTimeout(() => stream.push('data: {"event":"run.started","payload":{}}\n\n'), 50);

      // Simulate a split JSON payload across multiple network chunks
      setTimeout(() => stream.push('data: {"event":"message.del'), 100);
      setTimeout(() => stream.push('ta","payload":{"text":"Hel"}}\n\n'), 200);

      // Send the rest
      setTimeout(() => stream.push('data: {"event":"message.delta","payload":{"text":"lo"}}\n\n'), 300);
      setTimeout(() => {
        stream.push('data: {"event":"run.completed","payload":{}}\n\n');
        stream.push(null);
      }, 400);
    });

    await page.goto('/chat');
    await page.getByPlaceholder('Ask LYSTRA anything...').fill('Fragment test');
    await page.getByPlaceholder('Ask LYSTRA anything...').press('Enter');

    // UI should successfully reconstruct "Hello" without missing text
    const msg = page.getByText('Hello');
    await expect(msg).toBeVisible();
  });

  test('FE-84: Stream Reconnection Test', async ({ page }) => {
    let requestCount = 0;

    await page.route('**/api/v1/messages', async route => {
      requestCount++;
      const stream = new Readable({ read() { } });

      route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'text/event-stream' },
        body: stream as any
      });

      stream.push('data: {"event":"run.started","payload":{}}\n\n');

      if (requestCount === 1) {
        stream.push('data: {"event":"message.delta","payload":{"text":"First part."}}\n\n');
        // Abruptly close the stream with an error
        setTimeout(() => stream.destroy(new Error("Network drop")), 100);
      } else {
        // Upon reconnection, replay the missing part
        stream.push('data: {"event":"message.delta","payload":{"text":" Second part."}}\n\n');
        stream.push('data: {"event":"run.completed","payload":{}}\n\n');
        setTimeout(() => stream.push(null), 50);
      }
    });

    await page.goto('/chat');
    await page.getByPlaceholder('Ask LYSTRA anything...').fill('Reconnect test');
    await page.getByPlaceholder('Ask LYSTRA anything...').press('Enter');

    // Wait for the full reconstructed message
    const msg = page.getByText('First part. Second part.');
    await expect(msg).toBeVisible();
  });

  test('FE-85: Response Reconciliation Test', async ({ page }) => {
    await page.route('**/api/v1/messages', async route => {
      const stream = new Readable({ read() { } });
      route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'text/event-stream' },
        body: stream as any
      });

      stream.push('data: {"event":"run.started","payload":{}}\n\n');
      // The backend echoes the user message as 'message.accepted'
      stream.push('data: {"event":"message.accepted","payload":{"message":"Reconciliation check"}}\n\n');
      stream.push('data: {"event":"message.delta","payload":{"text":"Assistant replied"}}\n\n');
      stream.push('data: {"event":"run.completed","payload":{}}\n\n');
      stream.push(null);
    });

    await page.goto('/chat');
    await page.getByPlaceholder('Ask LYSTRA anything...').fill('Reconciliation check');
    await page.getByPlaceholder('Ask LYSTRA anything...').press('Enter');

    // Expected: 1 User message, 1 Assistant message (no duplicates)
    await expect(page.getByText('Reconciliation check')).toHaveCount(1);
    await expect(page.getByText('Assistant replied')).toHaveCount(1);
  });

  test('FE-86: Long Response Scroll Stability', async ({ page }) => {
    await page.route('**/api/v1/messages', async route => {
      const stream = new Readable({ read() { } });
      route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'text/event-stream' },
        body: stream as any
      });

      stream.push('data: {"event":"run.started","payload":{}}\n\n');

      // Stream an enormous payload very fast
      const hugeMarkdown = Array(100).fill('Here is a large block of text designed to test virtualization and scrolling stability.\n\n```python\nprint("Hello World")\n```\n\n').join('');

      let index = 0;
      const interval = setInterval(() => {
        if (index >= hugeMarkdown.length) {
          clearInterval(interval);
          stream.push('data: {"event":"run.completed","payload":{}}\n\n');
          stream.push(null);
          return;
        }
        const chunk = hugeMarkdown.slice(index, index + 500);
        stream.push(`data: {"event":"message.delta","payload":{"text":${JSON.stringify(chunk)}}}\n\n`);
        index += 500;
      }, 5);
    });

    await page.goto('/chat');
    await page.getByPlaceholder('Ask LYSTRA anything...').fill('Long string');
    await page.getByPlaceholder('Ask LYSTRA anything...').press('Enter');

    // Assert that the page does not freeze and the final block renders
    await expect(page.locator('.prose')).toBeVisible();
    await expect(page.locator('.prose')).toContainText('Hello World', { timeout: 15000 });
  });
});
