import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';

test.describe('Costs Page', () => {
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

  test('should display GPU cost, platform cost, and avoided cost as three separate tiles', async ({ page }) => {
    await setupSession(page);

    const mockCostsResponse = {
      daily: [
        {
          site_id: 'site-1',
          date: '2026-09-13',
          gpu_cost_usd: 10.5678,
          platform_cost_usd: 2.1234,
          avoided_cost_usd: 5.4321,
          batch_job_count: 15,
          local_job_count: 20,
          billed_seconds: 1800,
          local_duration_seconds: 900,
        },
      ],
      total: {
        gpu_cost_usd: 10.5678,
        platform_cost_usd: 2.1234,
        avoided_cost_usd: 5.4321,
        batch_job_count: 15,
        local_job_count: 20,
        billed_seconds: 1800,
        local_duration_seconds: 900,
      },
    };

    const mockSitesResponse = {
      sites: [
        { site_id: 'site-1', label: 'Site 1', disabled: false, created_at: '2026-01-01T00:00:00Z' },
        { site_id: 'site-2', label: 'Site 2', disabled: false, created_at: '2026-01-02T00:00:00Z' },
      ],
    };

    await page.route('**/admin/costs**', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockCostsResponse),
      });
    });

    await page.route('**/sites', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockSitesResponse),
      });
    });

    await page.goto(`${BASE_URL}/costs`);
    await page.waitForLoadState('networkidle');

    // Check for the three cost tiles - look for specific text patterns
    await expect(page.locator('text=Total GPU Cost').first()).toBeVisible();
    await expect(page.locator('div').filter({ hasText: /Total GPU Cost.*\$10\.5678/ }).first()).toBeVisible();

    await expect(page.locator('text=Total Platform Cost').first()).toBeVisible();
    await expect(page.locator('div').filter({ hasText: /Total Platform Cost.*\$2\.1234/ }).first()).toBeVisible();

    await expect(page.locator('text=Avoided Cost (Local Workers)').first()).toBeVisible();
    await expect(page.locator('div').filter({ hasText: /Avoided Cost.*\$5\.4321/ }).first()).toBeVisible();
  });

  test('should display daily cost table with one row per daily entry', async ({ page }) => {
    await setupSession(page);

    const mockCostsResponse = {
      daily: [
        {
          site_id: 'site-1',
          date: '2026-09-13',
          gpu_cost_usd: 10.5678,
          platform_cost_usd: 2.1234,
          avoided_cost_usd: 5.4321,
          batch_job_count: 15,
          local_job_count: 20,
          billed_seconds: 1800,
          local_duration_seconds: 900,
        },
        {
          site_id: 'site-1',
          date: '2026-09-12',
          gpu_cost_usd: 8.2500,
          platform_cost_usd: 1.5000,
          avoided_cost_usd: 4.1250,
          batch_job_count: 12,
          local_job_count: 18,
          billed_seconds: 1500,
          local_duration_seconds: 800,
        },
      ],
      total: {
        gpu_cost_usd: 18.8178,
        platform_cost_usd: 3.6234,
        avoided_cost_usd: 9.5571,
        batch_job_count: 27,
        local_job_count: 38,
        billed_seconds: 3300,
        local_duration_seconds: 1700,
      },
    };

    const mockSitesResponse = {
      sites: [
        { site_id: 'site-1', label: 'Site 1', disabled: false, created_at: '2026-01-01T00:00:00Z' },
      ],
    };

    await page.route('**/admin/costs**', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockCostsResponse),
      });
    });

    await page.route('**/sites', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockSitesResponse),
      });
    });

    await page.goto(`${BASE_URL}/costs`);
    await page.waitForLoadState('networkidle');

    // Check for table header
    await expect(page.locator('table.data-table th:has-text("Date")')).toBeVisible();

    // Check that two daily entries are displayed
    const tableRows = page.locator('table.data-table tbody tr');
    await expect(tableRows).toHaveCount(2);
  });

  test('should refetch with site_id parameter when site filter is changed', async ({ page }) => {
    await setupSession(page);

    const mockCostsResponse = {
      daily: [
        {
          site_id: 'site-1',
          date: '2026-09-13',
          gpu_cost_usd: 10.5678,
          platform_cost_usd: 2.1234,
          avoided_cost_usd: 5.4321,
          batch_job_count: 15,
          local_job_count: 20,
          billed_seconds: 1800,
          local_duration_seconds: 900,
        },
      ],
      total: {
        gpu_cost_usd: 10.5678,
        platform_cost_usd: 2.1234,
        avoided_cost_usd: 5.4321,
        batch_job_count: 15,
        local_job_count: 20,
        billed_seconds: 1800,
        local_duration_seconds: 900,
      },
    };

    const mockSitesResponse = {
      sites: [
        { site_id: 'site-1', label: 'Site 1', disabled: false, created_at: '2026-01-01T00:00:00Z' },
        { site_id: 'site-2', label: 'Site 2', disabled: false, created_at: '2026-01-02T00:00:00Z' },
      ],
    };

    await page.route('**/admin/costs**', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockCostsResponse),
      });
    });

    await page.route('**/sites', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockSitesResponse),
      });
    });

    await page.goto(`${BASE_URL}/costs`);
    await page.waitForLoadState('networkidle');

    // Select a site filter, waiting for the specific refetch it triggers
    // rather than networkidle: under parallel test load, the state
    // update -> re-render -> fetch dispatch can lag past a brief window
    // where the network already looks idle from the initial page load,
    // making networkidle resolve before the new request is even sent.
    //
    // Assert directly on the request waitForRequest already matched,
    // rather than re-checking the separate `requestedUrls` array the
    // route handler populates -- that push happens in an independent
    // listener with no ordering guarantee relative to waitForRequest's
    // own resolution, so re-checking it here raced against its own fill.
    const selectElement = page.locator('select');
    const [sitedFetch] = await Promise.all([
      page.waitForRequest((request) => request.url().includes('site_id=site-2')),
      selectElement.selectOption('site-2'),
    ]);

    expect(sitedFetch.url()).toContain('site_id=site-2');
  });

  test('should show empty state when daily array is empty', async ({ page }) => {
    await setupSession(page);

    const mockCostsResponse = {
      daily: [],
      total: {
        gpu_cost_usd: 0,
        platform_cost_usd: 0,
        avoided_cost_usd: 0,
        batch_job_count: 0,
        local_job_count: 0,
        billed_seconds: 0,
        local_duration_seconds: 0,
      },
    };

    const mockSitesResponse = {
      sites: [],
    };

    await page.route('**/admin/costs**', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockCostsResponse),
      });
    });

    await page.route('**/sites', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockSitesResponse),
      });
    });

    await page.goto(`${BASE_URL}/costs`);
    await page.waitForLoadState('networkidle');

    // Check for empty state message
    await expect(page.locator('text=No cost data available')).toBeVisible();

    // Verify no table rows are shown
    const tableRows = page.locator('table.data-table tbody tr');
    await expect(tableRows).toHaveCount(0);
  });

  test('should show error state when costs fetch fails', async ({ page }) => {
    await setupSession(page);

    const mockSitesResponse = {
      sites: [],
    };

    await page.route('**/admin/costs**', (route) => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' }),
      });
    });

    await page.route('**/sites', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockSitesResponse),
      });
    });

    await page.goto(`${BASE_URL}/costs`);
    await page.waitForLoadState('networkidle');

    // Check for error message
    await expect(page.locator('text=Error loading costs:')).toBeVisible();

    // Verify cost tiles are not shown
    await expect(page.locator('text=Total GPU Cost')).not.toBeVisible();
  });
});

test.describe('Dashboard Cost Tiles', () => {
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

  test('should display cost tiles on dashboard page', async ({ page }) => {
    await setupSession(page);

    const mockOverviewResponse = {
      counts: { pending: 2, claimed: 1, done: 42, failed: 0 },
      worker_breakdown: { local: 30, batch: 12 },
      avg_duration_seconds: 2.5,
      batch_queue_state: 'ENABLED',
      total_sampled_jobs: 42,
    };

    const mockJobsResponse = {
      jobs: [],
      next_token: null,
    };

    const mockCostsResponse = {
      daily: [],
      total: {
        gpu_cost_usd: 15.7890,
        platform_cost_usd: 3.2100,
        avoided_cost_usd: 8.5000,
        batch_job_count: 100,
        local_job_count: 150,
        billed_seconds: 3600,
        local_duration_seconds: 1800,
      },
    };

    await page.route('**/admin/overview', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockOverviewResponse),
      });
    });

    await page.route('**/admin/jobs', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockJobsResponse),
      });
    });

    await page.route('**/admin/costs**', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockCostsResponse),
      });
    });

    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');

    // Check for cost tiles on dashboard
    await expect(page.locator('text=Cloud GPU Cost')).toBeVisible();
    await expect(page.locator('text=$15.7890')).toBeVisible();

    await expect(page.locator('text=Saved via Local Workers')).toBeVisible();
    await expect(page.locator('text=$8.5000')).toBeVisible();

    // Verify the tiles link to /costs
    const costTiles = page.locator('a[href="/costs"]');
    expect(await costTiles.count()).toBeGreaterThan(0);

    // The "right now" live-snapshot section (including the AWS Batch
    // Queue / Cloud Fallback tile) was removed entirely -- the range-scoped
    // tiles below supersede it.
    await expect(page.locator('text=AWS Batch Queue')).not.toBeVisible();
    await expect(page.locator('text=Cloud Fallback')).not.toBeVisible();
  });
});
