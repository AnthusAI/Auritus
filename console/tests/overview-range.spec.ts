import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';

test.describe('Overview Date Range', () => {
  async function setupSession(page: any) {
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

  const mockOverviewResponse = {
    counts: { pending: 3, claimed: 1, done: 42, failed: 2 },
    worker_breakdown: { local: 30, batch: 12 },
    avg_duration_seconds: 12.4,
    batch_queue_state: 'ENABLED',
    total_sampled_jobs: 42,
  };

  const mockJobsResponse = { jobs: [], next_token: null };

  function costsResponseFor(local: number, cloud: number) {
    return {
      daily: [],
      total: {
        gpu_cost_usd: 1.23,
        platform_cost_usd: 0.01,
        avoided_cost_usd: 0.45,
        batch_job_count: cloud,
        local_job_count: local,
        billed_seconds: 100,
        local_duration_seconds: 50,
      },
    };
  }

  async function setupRoutes(page: any, requestedUrls: string[]) {
    await page.route('**/admin/overview', (route: any) => {
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(mockOverviewResponse) });
    });
    await page.route('**/admin/jobs', (route: any) => {
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(mockJobsResponse) });
    });
    await page.route('**/admin/costs**', (route: any) => {
      requestedUrls.push(route.request().url());
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(costsResponseFor(30, 12)) });
    });
  }

  function todayISO(): string {
    return new Date().toISOString().slice(0, 10);
  }

  test('default load fires /admin/costs with from=to=today', async ({ page }) => {
    await setupSession(page);
    const requestedUrls: string[] = [];
    await setupRoutes(page, requestedUrls);

    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');

    expect(requestedUrls.length).toBeGreaterThan(0);
    const url = new URL(requestedUrls[requestedUrls.length - 1]);
    const today = todayISO();
    expect(url.searchParams.get('from')).toBe(today);
    expect(url.searchParams.get('to')).toBe(today);
  });

  test('switching to 7 days refetches with a 7-day range', async ({ page }) => {
    await setupSession(page);
    const requestedUrls: string[] = [];
    await setupRoutes(page, requestedUrls);

    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');

    const [request] = await Promise.all([
      page.waitForRequest((req: any) => req.url().includes('/admin/costs')),
      page.click('button:has-text("7 days")'),
    ]);

    const url = new URL(request.url());
    const today = new Date();
    const expectedFrom = new Date(today);
    expectedFrom.setDate(expectedFrom.getDate() - 6);
    expect(url.searchParams.get('from')).toBe(expectedFrom.toISOString().slice(0, 10));
    expect(url.searchParams.get('to')).toBe(today.toISOString().slice(0, 10));
  });

  test('custom range only fetches once both dates are set', async ({ page }) => {
    await setupSession(page);
    const requestedUrls: string[] = [];
    await setupRoutes(page, requestedUrls);

    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');

    await page.click('button:has-text("Custom")');
    const countBeforeDates = requestedUrls.length;

    const dateInputs = page.locator('input[type="date"]');
    await dateInputs.nth(0).fill('2026-09-01');
    // Only the start date is set -- no new fetch should fire yet.
    await page.waitForTimeout(300);
    expect(requestedUrls.length).toBe(countBeforeDates);

    const [request] = await Promise.all([
      page.waitForRequest((req: any) => req.url().includes('/admin/costs')),
      dateInputs.nth(1).fill('2026-09-10'),
    ]);

    const url = new URL(request.url());
    expect(url.searchParams.get('from')).toBe('2026-09-01');
    expect(url.searchParams.get('to')).toBe('2026-09-10');
  });

  test('donut chart shows correct local/cloud counts', async ({ page }) => {
    await setupSession(page);
    const requestedUrls: string[] = [];
    await setupRoutes(page, requestedUrls);

    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');

    await expect(page.getByTestId('donut-local-count')).toHaveText('30');
    await expect(page.getByTestId('donut-cloud-count')).toHaveText('12');
  });

  test('right now and for-selected-range sections are both visible and correctly scoped', async ({ page }) => {
    await setupSession(page);
    const requestedUrls: string[] = [];
    await setupRoutes(page, requestedUrls);

    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');

    await expect(page.locator('text=Right now')).toBeVisible();
    await expect(page.locator('text=Live snapshot')).toBeVisible();
    await expect(page.locator('text=For selected range')).toBeVisible();

    const liveSnapshot = page.getByTestId('section-live-snapshot');
    await expect(liveSnapshot.locator('text=Pending')).toBeVisible();
    await expect(liveSnapshot.locator('text=Claimed')).toBeVisible();
    await expect(liveSnapshot.locator('text=Failed')).toBeVisible();
    await expect(liveSnapshot.locator('text=Cloud Fallback')).toBeVisible();

    const rangeScoped = page.getByTestId('section-range-scoped');
    await expect(rangeScoped.locator('text=Completed Jobs')).toBeVisible();
    await expect(rangeScoped.locator('text=Local vs Cloud')).toBeVisible();
    await expect(rangeScoped.locator('text=Cloud GPU Cost')).toBeVisible();
  });
});
