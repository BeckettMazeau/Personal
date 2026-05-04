import { test, expect } from '@playwright/test';

test.describe('FileCutter Review Interface', () => {
  test('should load files and complete the safety lock deletion flow', async ({ page }) => {
    // Mock the API response so we don't depend on the backend
    await page.route('http://localhost:8000/files', async route => {
      const json = [
        { path: '/fake/path/file1.txt', filename: 'file1.txt', size_mb: 1.2, confidence_score: 3 },
        { path: '/fake/path/file2.pdf', filename: 'file2.pdf', size_mb: 0.5, confidence_score: 1 }
      ];
      await route.fulfill({ json });
    });

    await page.route('http://localhost:8000/cleanup', async route => {
      await route.fulfill({ json: { status: "success", deleted_count: 1 } });
    });

    // 1. Navigate to the app
    await page.goto('/');

    // 2. Wait for loading to finish (scanning, shallow, deep)
    await expect(page.locator('text=Scanning directory...')).toBeVisible();

    // We can't rely on 'Running deep AI assessment...' because the text might change too fast depending on API response.
    // Instead, we wait for the main interface to load.
    await expect(page.locator('text=FileCutter Review')).toBeVisible({ timeout: 15000 });

    // 3. Select files using "Quick Select: All Level 3"
    await page.click('button:has-text("All Level 3 (Safe to Delete)")');

    // Verify selection (should be > 0 files selected)
    const selectedText = await page.locator('header').textContent();
    expect(selectedText).toMatch(/[1-9]\d* files selected/);

    // 4. Click Execute Cleanup
    const executeButton = page.locator('button:has-text("Execute Cleanup")');
    await expect(executeButton).not.toBeDisabled();
    await executeButton.click();

    // 5. Verify Safety Lock Modal appears
    const modal = page.locator('.modal-content');
    await expect(modal).toBeVisible();
    await expect(modal.locator('h2')).toHaveText('Safety Lock');

    // 6. Complete confirmation
    // Type DELETE
    await modal.locator('input[type="text"]').fill('DELETE');

    // Proceed button should now be enabled
    const proceedButton = modal.locator('button:has-text("Confirm Execution")');
    await expect(proceedButton).not.toBeDisabled();

    // Accept the alert dialog that appears after execution
    page.on('dialog', async dialog => {
      expect(dialog.message()).toBe('Cleanup executed successfully');
      await dialog.accept();
    });

    // Click proceed
    await proceedButton.click();

    // 7. Verify modal closes and selection is cleared
    await expect(modal).not.toBeVisible();
    await expect(page.locator('text=0 files selected')).toBeVisible();
  });
});
