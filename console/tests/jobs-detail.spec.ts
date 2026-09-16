import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';
const HASH = 'test-hash-123abc';

test.describe('Job Detail Page Error Handling', () => {
  async function setupSession(page: any) {
    // Set up authentication session before first navigation
    await page.addInitScript(() => {
      localStorage.setItem(
        'auritus_console_session',
        JSON.stringify({
          email: 'operator@example.com',
          accessToken: 'test-access-token',
          idToken: 'test-id-token',
          expiresAt: 9999999999999,
        })
      );
    });
  }

  test('should show error message when job detail fetch fails with HTTP 500 error', async ({ page }) => {
    await setupSession(page);
    // Mock the API to return an HTTP 500 error
    await page.route('**/admin/jobs/**', (route) => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' }),
      });
    });

    // Navigate to the job detail page
    await page.goto(`${BASE_URL}/jobs/detail?hash=${HASH}`);

    // Wait for loading to complete
    await page.waitForLoadState('networkidle');

    // Check for error message
    await expect(page.locator('text=Failed to load job details')).toBeVisible();

    // Verify no audio player is shown (no job data)
    await expect(page.locator('audio')).not.toBeVisible();

    // Verify no telemetry card is shown
    await expect(page.locator('text=Execution Telemetry')).not.toBeVisible();

    // Verify back link is available
    await expect(page.locator('a:has-text("Back to Job Explorer")')).toBeVisible();
  });

  test('should show error message when job detail fetch fails with network timeout', async ({ page }) => {
    await setupSession(page);

    // Mock the API to simulate a network timeout
    await page.route('**/admin/jobs/**', (route) => {
      route.abort('timedout');
    });

    // Navigate to the job detail page
    await page.goto(`${BASE_URL}/jobs/detail?hash=${HASH}`);

    // Wait for loading to complete
    await page.waitForLoadState('networkidle');

    // Check for error message
    await expect(page.locator('text=Failed to load job details')).toBeVisible();

    // Verify no audio player is shown
    await expect(page.locator('audio')).not.toBeVisible();

    // Verify no telemetry card is shown
    await expect(page.locator('text=Execution Telemetry')).not.toBeVisible();
  });

  test('should show "not found" message when no hash is provided', async ({ page }) => {
    await setupSession(page);

    // Navigate without hash parameter
    await page.goto(`${BASE_URL}/jobs/detail`);

    // Check for "not found" message (distinct from fetch error)
    await expect(page.locator('text=No content hash provided or job not found')).toBeVisible();

    // Verify no error box is shown
    await expect(page.locator('text=Failed to load job details')).not.toBeVisible();

    // Verify back link is available
    await expect(page.locator('a:has-text("Back to Job Explorer")')).toBeVisible();
  });

  test('should display job details when fetch succeeds', async ({ page }) => {
    await setupSession(page);

    const mockJob = {
      content_hash: HASH,
      status: 'done',
      worker_type: 'local',
      claimed_by: 'local:node-1:abcdef',
      tts_backend: 'kokoro',
      voice_id: 'af_heart',
      text: 'Test text',
      name: 'Test Job',
      byline: 'Test Author',
      created_at: '2026-09-13T14:10:00Z',
      claimed_at: '2026-09-13T14:10:01Z',
      completed_at: '2026-09-13T14:10:05Z',
      duration_seconds: 4.2,
      audio_url: 'https://cdn.example.com/audio/sample.mp3',
    };

    // Mock the API to return a successful job
    await page.route('**/admin/jobs/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockJob),
      });
    });

    // Navigate to the job detail page
    await page.goto(`${BASE_URL}/jobs/detail?hash=${HASH}`);

    // Wait for the job data to load
    await page.waitForLoadState('networkidle');

    // Verify job details are displayed
    await expect(page.locator('h1:has-text("Job Inspection")')).toBeVisible();
    await expect(page.locator('.badge.badge-done')).toBeVisible();
    await expect(page.locator('.card:first-of-type').locator('text=Test text')).toBeVisible();

    // Verify telemetry card is shown
    await expect(page.locator('h3:has-text("Execution Telemetry")')).toBeVisible();

    // Verify audio player is shown
    await expect(page.locator('audio')).toBeVisible();

    // Verify no error message is shown
    await expect(page.locator('text=Failed to load job details')).not.toBeVisible();
  });
});
