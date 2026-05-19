import { test, expect } from '@playwright/test';
import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

test.describe('E2E Full Flow', () => {
  let backendProcess;
  let frontendProcess;

  test.beforeAll(async () => {
    // Start backend
    const backendDir = path.join(__dirname, '../../backend');
    backendProcess = spawn('python3', ['-m', 'uvicorn', 'main:app', '--port', '8000'], {
      cwd: backendDir,
      env: { ...process.env, PYTHONPATH: backendDir }
    });

    // Start frontend manually in E2E since we are running playwright outside frontend dir
    const frontendDir = path.join(__dirname, '../../frontend');
    frontendProcess = spawn('npm', ['run', 'dev'], {
      cwd: frontendDir
    });

    // Give them a moment to start
    await new Promise(resolve => setTimeout(resolve, 5000));
  });

  test.afterAll(async () => {
    // Kill processes
    if (backendProcess) backendProcess.kill();
    if (frontendProcess) frontendProcess.kill();
  });

  test('should run full flow successfully with simulated API', async ({ page }) => {
    await page.route('http://localhost:8000/files', async route => {
      const json = [
        { path: '/fake/path/garbage1.exe', filename: 'garbage1.exe', size_mb: 1.2, confidence_score: 3 },
        { path: '/fake/path/important.pdf', filename: 'important.pdf', size_mb: 0.5, confidence_score: 1 }
      ];
      await route.fulfill({ json });
    });

    await page.route('http://localhost:8000/cleanup', async route => {
      await route.fulfill({ json: { status: "success", deleted_count: 1 } });
    });

    await page.goto('/');

    await expect(page.locator('text=Scanning directory...')).toBeVisible();
    await expect(page.locator('text=FileCutter Review')).toBeVisible({ timeout: 15000 });

    await page.click('button:has-text("All Level 3 (Safe to Delete)")');

    let selectedText = await page.locator('header').textContent();
    expect(selectedText).toMatch(/[1-9]\d* files selected/);

    const executeButton = page.locator('button:has-text("Execute Cleanup")');
    await expect(executeButton).not.toBeDisabled();
    await executeButton.click();

    const modal = page.locator('.modal-content');
    await expect(modal).toBeVisible();
    await expect(modal.locator('h2')).toHaveText('Safety Lock');

    await modal.locator('input[type="text"]').fill('DELETE');
    const proceedButton = modal.locator('button:has-text("Confirm Execution")');
    await expect(proceedButton).not.toBeDisabled();

    page.on('dialog', async dialog => {
      expect(dialog.message()).toBe('Cleanup executed successfully');
      await dialog.accept();
    });

    await proceedButton.click();

    await expect(modal).not.toBeVisible();
    await expect(page.locator('text=0 files selected')).toBeVisible();
  });
});
