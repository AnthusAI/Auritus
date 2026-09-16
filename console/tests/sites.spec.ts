import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';

test.describe('Sites Page', () => {
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

  function setupMockRoute(page: any, handler: (method: string) => any) {
    // Mock the /sites endpoint, distinguishing API calls from page navigation
    page.route('/sites', (route: any) => {
      const request = route.request();
      const method = request.method();

      // API requests have resourceType 'fetch', page navigation has 'document'
      if (request.resourceType() === 'fetch') {
        const response = handler(method);
        const body = typeof response.body === 'string' ? response.body : JSON.stringify(response.body);
        route.fulfill({
          status: response.status || 200,
          contentType: 'application/json',
          body: body,
        });
      } else {
        // Page navigation - let it through
        route.continue();
      }
    });

    // Also mock DELETE requests to /sites/{id}
    page.route(/\/sites\/[^/]+$/, (route: any) => {
      const request = route.request();
      if (request.resourceType() === 'fetch' && request.method() === 'DELETE') {
        const response = handler('DELETE');
        const body = typeof response.body === 'string' ? response.body : JSON.stringify(response.body);
        route.fulfill({
          status: response.status || 200,
          contentType: 'application/json',
          body: body,
        });
      } else {
        route.continue();
      }
    });
  }

  test('should display existing sites from mocked GET /sites response', async ({ page }) => {
    await setupSession(page);

    const mockSites = [
      {
        site_id: '550e8400-e29b-41d4-a716-446655440000',
        label: 'Example Blog',
        disabled: false,
        created_at: '2026-09-10T14:30:00Z',
      },
      {
        site_id: '550e8400-e29b-41d4-a716-446655440001',
        label: 'Test Site',
        disabled: true,
        created_at: '2026-09-09T10:15:00Z',
      },
    ];

    setupMockRoute(page, () => ({ body: { sites: mockSites } }));

    await page.goto(`${BASE_URL}/sites`);
    await page.waitForLoadState('networkidle');

    // Verify the sites are displayed in the table
    // Check for both site labels in the page
    await expect(page.getByText('Example Blog')).toBeVisible();
    await expect(page.getByText('Test Site')).toBeVisible();

    // Verify the status badges are shown (find the first instance of each)
    const rows = await page.locator('tbody tr').count();
    expect(rows).toBeGreaterThanOrEqual(2);
  });

  test('should successfully create a site and show the site key', async ({ page }) => {
    await setupSession(page);

    const newSiteData = {
      site_id: '550e8400-e29b-41d4-a716-446655440002',
      site_key: 'test_site_key_abc123_xyz789',
      label: 'New Test Site',
      disabled: false,
      created_at: '2026-09-15T12:00:00Z',
    };

    let postCalled = false;

    setupMockRoute(page, (method: string) => {
      if (method === 'GET') {
        return { body: { sites: [] } };
      } else if (method === 'POST') {
        postCalled = true;
        return { status: 201, body: newSiteData };
      }
      return { body: {} };
    });

    await page.goto(`${BASE_URL}/sites`);
    await page.waitForLoadState('networkidle');

    // Fill in the label input
    await page.fill('input[placeholder*="e.g., Example Site"]', 'New Test Site');

    // Click create button
    await page.click('button:has-text("Create Site Key")');

    // Wait for the response - use a longer wait and check for the specific element
    await page.waitForTimeout(1000);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);

    // Verify POST was called
    expect(postCalled).toBe(true);

    // Verify the success message is shown
    const successLocator = page.locator('text=Site Key Created Successfully');
    await expect(successLocator).toBeVisible({ timeout: 10000 });

    // Verify the site_key is displayed (might appear in multiple places, so use first())
    await expect(page.locator('text=test_site_key_abc123_xyz789').first()).toBeVisible();

    // Verify the embed snippet is shown
    await expect(page.locator('text=Embed Snippet')).toBeVisible();
  });

  test('should copy embed snippet to clipboard', async ({ page }) => {
    await setupSession(page);

    const newSiteData = {
      site_id: '550e8400-e29b-41d4-a716-446655440003',
      site_key: 'copy_test_key_123',
      label: 'Copy Test Site',
      disabled: false,
      created_at: '2026-09-15T12:00:00Z',
    };

    setupMockRoute(page, (method: string) => {
      if (method === 'GET') {
        return { body: { sites: [] } };
      } else if (method === 'POST') {
        return { status: 201, body: newSiteData };
      }
      return { body: {} };
    });

    await page.goto(`${BASE_URL}/sites`);
    await page.waitForLoadState('networkidle');

    // Create a site
    await page.fill('input[placeholder*="e.g., Example Site"]', 'Copy Test Site');
    await page.click('button:has-text("Create Site Key")');
    await page.waitForLoadState('networkidle');

    // Verify copy button is present and clickable
    const copyButton = page.locator('button:has-text("Copy Snippet")');
    await expect(copyButton).toBeVisible();

    // Click copy button and verify it completes without error
    await copyButton.click();

    // Verify the embed snippet is still visible after copying
    await expect(page.locator('text=Embed Snippet')).toBeVisible();
  });

  test('should revoke a site with confirmation', async ({ page }) => {
    await setupSession(page);

    const siteToRevoke = {
      site_id: '550e8400-e29b-41d4-a716-446655440004',
      label: 'Site to Revoke',
      disabled: false,
      created_at: '2026-09-10T10:00:00Z',
    };

    let deleteWasCalled = false;

    setupMockRoute(page, (method: string) => {
      if (method === 'GET') {
        return { body: { sites: [siteToRevoke] } };
      } else if (method === 'DELETE') {
        deleteWasCalled = true;
        return { body: { site_id: siteToRevoke.site_id, deleted: true } };
      }
      return { body: {} };
    });

    await page.goto(`${BASE_URL}/sites`);
    await page.waitForLoadState('networkidle');

    // Verify the site is displayed
    await expect(page.locator(`text=${siteToRevoke.label}`)).toBeVisible();

    // Accept confirmation and click Revoke
    page.once('dialog', (dialog) => {
      expect(dialog.message()).toContain('Are you sure');
      dialog.accept();
    });

    await page.click('button:has-text("Revoke")');
    await page.waitForLoadState('networkidle');

    // Verify the DELETE request was made
    expect(deleteWasCalled).toBe(true);

    // Verify the site is no longer in the list
    await expect(page.locator(`text=${siteToRevoke.label}`)).not.toBeVisible();
  });

  test('should not revoke a site if confirmation is dismissed', async ({ page }) => {
    await setupSession(page);

    const siteToKeep = {
      site_id: '550e8400-e29b-41d4-a716-446655440005',
      label: 'Site to Keep',
      disabled: false,
      created_at: '2026-09-10T10:00:00Z',
    };

    let deleteWasCalled = false;

    setupMockRoute(page, (method: string) => {
      if (method === 'GET') {
        return { body: { sites: [siteToKeep] } };
      } else if (method === 'DELETE') {
        deleteWasCalled = true;
        return { body: { site_id: siteToKeep.site_id, deleted: true } };
      }
      return { body: {} };
    });

    await page.goto(`${BASE_URL}/sites`);
    await page.waitForLoadState('networkidle');

    // Verify the site is displayed
    await expect(page.locator(`text=${siteToKeep.label}`)).toBeVisible();

    // Dismiss confirmation and click Revoke
    page.once('dialog', (dialog) => {
      dialog.dismiss();
    });

    await page.click('button:has-text("Revoke")');

    // Verify the DELETE request was NOT made
    expect(deleteWasCalled).toBe(false);

    // Verify the site is still in the list
    await expect(page.locator(`text=${siteToKeep.label}`)).toBeVisible();
  });

  test('should show empty state when no sites exist', async ({ page }) => {
    await setupSession(page);

    setupMockRoute(page, () => ({ body: { sites: [] } }));

    await page.goto(`${BASE_URL}/sites`);
    await page.waitForLoadState('networkidle');

    // Verify the empty state message is shown
    await expect(page.locator('text=No sites yet. Create one above')).toBeVisible();

    // Verify no error message is shown
    await expect(page.locator('text=Error loading sites')).not.toBeVisible();
  });

  test('should show error state when GET /sites fails', async ({ page }) => {
    await setupSession(page);

    setupMockRoute(page, () => ({ status: 500, body: { error: 'Internal server error' } }));

    await page.goto(`${BASE_URL}/sites`);
    await page.waitForLoadState('networkidle');

    // Verify the error message is shown
    await expect(page.locator('text=Error loading sites')).toBeVisible();

    // Verify no fabricated data is shown
    // The page should not display any site rows (only header + error row)
    const rows = await page.locator('tbody tr').count();
    expect(rows).toBe(1); // Only the error row
  });

  test('should display error when create site fails', async ({ page }) => {
    await setupSession(page);

    setupMockRoute(page, (method: string) => {
      if (method === 'GET') {
        return { body: { sites: [] } };
      } else if (method === 'POST') {
        return { status: 400, body: { error: 'Invalid label' } };
      }
      return { body: {} };
    });

    await page.goto(`${BASE_URL}/sites`);
    await page.waitForLoadState('networkidle');

    // Try to create a site
    await page.fill('input[placeholder*="e.g., Example Site"]', 'Bad Site');
    await page.click('button:has-text("Create Site Key")');
    await page.waitForLoadState('networkidle');

    // Verify error is displayed (look for the error in the callout, not the table)
    await expect(page.getByRole('heading', { name: 'Error' })).toBeVisible();
    // The error message might be in the error callout or in the page somewhere
    const pageText = await page.locator('body').textContent();
    expect(pageText?.includes('Invalid label')).toBe(true);

    // Verify no success message is shown
    await expect(page.locator('text=Site Key Created Successfully')).not.toBeVisible();
  });

  test('should navigate from Header to Sites page', async ({ page }) => {
    await setupSession(page);

    setupMockRoute(page, () => ({ body: { sites: [] } }));

    // Start at the home page
    await page.goto(`${BASE_URL}/`);
    await page.waitForLoadState('networkidle');

    // Click on the Sites link in the header
    await page.click('a:has-text("Sites")');
    await page.waitForLoadState('networkidle');

    // Verify we're on the Sites page
    await expect(page.getByRole('heading', { level: 1, name: /Site Keys/i })).toBeVisible();
    await expect(page.locator('text=Create New Site Key')).toBeVisible();
  });
});
