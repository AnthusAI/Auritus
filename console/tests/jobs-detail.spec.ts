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

test.describe('Job Detail Page Actions', () => {
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

  test('should delete a done job when confirmation is accepted', async ({ page }) => {
    await setupSession(page);

    const mockJob = {
      content_hash: HASH,
      status: 'done',
      worker_type: 'local',
      claimed_by: 'local:node-1:abcdef',
      tts_backend: 'kokoro',
      voice_id: 'af_heart',
      text: 'Test text',
      created_at: '2026-09-13T14:10:00Z',
      claimed_at: '2026-09-13T14:10:01Z',
      completed_at: '2026-09-13T14:10:05Z',
      duration_seconds: 4.2,
      audio_url: 'https://cdn.example.com/audio/sample.mp3',
    };

    // Set up route for DELETE
    await page.route(`**/admin/jobs/${HASH}`, async (route) => {
      if (route.request().method() === 'DELETE') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ content_hash: HASH, deleted: true }),
        });
      } else if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockJob),
        });
      }
    });

    // Navigate to the job detail page
    await page.goto(`${BASE_URL}/jobs/detail?hash=${HASH}`);
    await page.waitForLoadState('networkidle');

    // Accept the delete confirmation
    page.on('dialog', (dialog: any) => {
      dialog.accept();
    });

    // Click delete button
    await page.locator('button:has-text("Delete Job")').click();

    // Verify we're redirected to /jobs
    await page.waitForURL(`${BASE_URL}/jobs`);
    await expect(page).toHaveURL(`${BASE_URL}/jobs`);
  });

  test('should not delete a job when confirmation is dismissed', async ({ page }) => {
    await setupSession(page);

    const mockJob = {
      content_hash: HASH,
      status: 'done',
      worker_type: 'local',
      tts_backend: 'kokoro',
      voice_id: 'af_heart',
      text: 'Test text',
      created_at: '2026-09-13T14:10:00Z',
      claimed_at: '2026-09-13T14:10:01Z',
      completed_at: '2026-09-13T14:10:05Z',
      duration_seconds: 4.2,
      audio_url: 'https://cdn.example.com/audio/sample.mp3',
    };

    // Mock the API
    await page.route(`**/admin/jobs/${HASH}`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockJob),
      });
    });

    // Navigate to the job detail page
    await page.goto(`${BASE_URL}/jobs/detail?hash=${HASH}`);
    await page.waitForLoadState('networkidle');

    // Dismiss the delete confirmation
    page.on('dialog', (dialog: any) => {
      dialog.dismiss();
    });

    // Click delete button
    await page.locator('button:has-text("Delete Job")').click();

    // Wait a moment for any navigation to occur (it shouldn't)
    await page.waitForTimeout(500);

    // Verify we're still on the job detail page
    await expect(page).toHaveURL(/jobs\/detail/);

    // Verify the job details are still shown
    await expect(page.locator('h1:has-text("Job Inspection")')).toBeVisible();
  });

  test('should regenerate a done job and update status to pending', async ({ page }) => {
    await setupSession(page);

    const mockJobDone = {
      content_hash: HASH,
      status: 'done',
      worker_type: 'local',
      tts_backend: 'kokoro',
      voice_id: 'af_heart',
      text: 'Test text',
      created_at: '2026-09-13T14:10:00Z',
      completed_at: '2026-09-13T14:10:05Z',
      duration_seconds: 4.2,
      audio_url: 'https://cdn.example.com/audio/sample.mp3',
    };

    const mockJobPending = {
      ...mockJobDone,
      status: 'pending',
      audio_url: undefined,
      completed_at: undefined,
      duration_seconds: undefined,
    };

    let postCount = 0;
    let getCount = 0;

    // Mock the API
    await page.route(`**/admin/jobs/${HASH}**`, async (route) => {
      const method = route.request().method();

      if (method === 'POST') {
        postCount++;
        // POST request for regenerate
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ content_hash: HASH, status: 'pending' }),
        });
      } else if (method === 'GET') {
        getCount++;
        // GET request for job detail - return pending after POST
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(postCount === 0 ? mockJobDone : mockJobPending),
        });
      }
    });

    // Navigate to the job detail page
    await page.goto(`${BASE_URL}/jobs/detail?hash=${HASH}`);
    await page.waitForLoadState('networkidle');

    // Verify initial status is done
    await expect(page.locator('.badge.badge-done')).toBeVisible();
    await expect(page.locator('audio')).toBeVisible();

    // Click regenerate button
    await page.locator('button:has-text("Regenerate")').click();

    // Wait for the action to complete and re-fetch
    await page.waitForLoadState('networkidle');

    // Verify status updated to pending
    await expect(page.locator('.badge.badge-pending')).toBeVisible();

    // Verify audio player is no longer shown
    await expect(page.locator('audio')).not.toBeVisible();

    // Verify "No audio artifact available" message is shown
    await expect(page.locator('text=No audio artifact available')).toBeVisible();
  });

  test('should retry a failed job and update status to pending', async ({ page }) => {
    await setupSession(page);

    const mockJobFailed = {
      content_hash: HASH,
      status: 'failed',
      worker_type: 'local',
      tts_backend: 'kokoro',
      voice_id: 'af_heart',
      text: 'Test text',
      created_at: '2026-09-13T14:10:00Z',
      claimed_at: '2026-09-13T14:10:01Z',
      failed_at: '2026-09-13T14:10:05Z',
      error_message: 'Connection timeout',
    };

    const mockJobPending = {
      ...mockJobFailed,
      status: 'pending',
      claimed_at: undefined,
      failed_at: undefined,
      error_message: undefined,
    };

    let postCount = 0;

    // Mock the API
    await page.route(`**/admin/jobs/${HASH}**`, async (route) => {
      const method = route.request().method();

      if (method === 'POST') {
        postCount++;
        // POST request for retry
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ content_hash: HASH, status: 'pending' }),
        });
      } else if (method === 'GET') {
        // GET request for job detail
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(postCount === 0 ? mockJobFailed : mockJobPending),
        });
      }
    });

    // Navigate to the job detail page
    await page.goto(`${BASE_URL}/jobs/detail?hash=${HASH}`);
    await page.waitForLoadState('networkidle');

    // Verify initial status is failed
    await expect(page.locator('.badge.badge-failed')).toBeVisible();
    // Check for error message in the telemetry card
    await expect(page.locator('.card:nth-child(2) >> text=Connection timeout')).toBeVisible();

    // Click retry button
    await page.locator('button:has-text("Retry")').click();

    // Wait for the action to complete and re-fetch
    await page.waitForLoadState('networkidle');

    // Verify status updated to pending
    await expect(page.locator('.badge.badge-pending')).toBeVisible();

    // Verify error message is no longer shown
    await expect(page.locator('text=Connection timeout')).not.toBeVisible();
  });

  test('should not show regenerate button for pending job', async ({ page }) => {
    await setupSession(page);

    const mockJob = {
      content_hash: HASH,
      status: 'pending',
      worker_type: 'local',
      tts_backend: 'kokoro',
      voice_id: 'af_heart',
      text: 'Test text',
      created_at: '2026-09-13T14:10:00Z',
    };

    // Mock the API
    await page.route(`**/admin/jobs/${HASH}`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockJob),
      });
    });

    // Navigate to the job detail page
    await page.goto(`${BASE_URL}/jobs/detail?hash=${HASH}`);
    await page.waitForLoadState('networkidle');

    // Verify no regenerate button
    await expect(page.locator('button:has-text("Regenerate")')).not.toBeVisible();

    // Verify no retry button
    await expect(page.locator('button:has-text("Retry")')).not.toBeVisible();
    await expect(page.locator('button:has-text("Release")')).not.toBeVisible();

    // Verify delete button is still shown
    await expect(page.locator('button:has-text("Delete Job")')).toBeVisible();
  });

  test('should show force-release option when retrying a claimed job returns live claim conflict', async ({ page }) => {
    await setupSession(page);

    const mockJob = {
      content_hash: HASH,
      status: 'claimed',
      worker_type: 'batch',
      claimed_by: 'batch:worker-1:xyz123',
      tts_backend: 'kokoro',
      voice_id: 'af_heart',
      text: 'Test text',
      created_at: '2026-09-13T14:10:00Z',
      claimed_at: '2026-09-13T14:10:01Z',
    };

    const mockJobPending = {
      ...mockJob,
      status: 'pending',
      claimed_at: undefined,
    };

    let retryAttempts = 0;

    // Mock all requests to /admin/jobs/{hash}*
    await page.route(`**/admin/jobs/${HASH}**`, async (route) => {
      const method = route.request().method();
      const url = route.request().url();

      if (method === 'GET') {
        // Return the job - use pending version if we've already retried with force
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(retryAttempts > 1 ? mockJobPending : mockJob),
        });
      } else if (method === 'POST' && url.includes('/retry')) {
        retryAttempts++;
        const body = route.request().postData();
        const hasForce = body && JSON.parse(body).force === true;

        if (retryAttempts === 1 && !hasForce) {
          // First attempt without force - return conflict
          await route.fulfill({
            status: 409,
            contentType: 'application/json',
            body: JSON.stringify({ error: 'claim_still_live' }),
          });
        } else if (hasForce) {
          // Second attempt with force - succeed
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ content_hash: HASH, status: 'pending' }),
          });
        }
      }
    });

    // Navigate to the job detail page
    await page.goto(`${BASE_URL}/jobs/detail?hash=${HASH}`);
    await page.waitForLoadState('networkidle');

    // Verify status is claimed and release button is shown
    await expect(page.locator('.badge.badge-claimed')).toBeVisible();
    await expect(page.locator('button:has-text("Release")')).toBeVisible();

    // Click release button (without force)
    await page.locator('button:has-text("Release")').click();

    // Wait a moment for the error message to appear
    await page.waitForTimeout(500);

    // Wait for the conflict error to appear
    await expect(page.locator('text=This job has an active claim. Force-release to override it.')).toBeVisible();

    // Verify force-release button appears
    await expect(page.locator('button:has-text("Force-release")')).toBeVisible();

    // Click force-release button
    await page.locator('button:has-text("Force-release")').click();

    // Wait for the action to complete and re-fetch
    await page.waitForLoadState('networkidle');

    // Verify no error message is shown anymore
    await expect(page.locator('text=This job has an active claim')).not.toBeVisible();

    // Verify status updated to pending
    await expect(page.locator('.badge.badge-pending')).toBeVisible();
  });
});
