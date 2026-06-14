import { test, expect } from '@playwright/test';

test('lineup analysis renders sliders and results table', async ({ page }) => {
  await page.goto('/apps/lineup-analysis');

  // Page title chrome
  await expect(page.getByText('Model Config').first()).toBeVisible();

  // Config form has expected knobs (mono labels with field keys)
  await expect(page.getByText('three_point_emphasis')).toBeVisible();
  await expect(page.getByText('rapm_lambda')).toBeVisible();

  // Sliders rendered via Radix → role=slider
  const sliders = page.getByRole('slider');
  await expect(sliders.first()).toBeVisible();
  expect(await sliders.count()).toBeGreaterThanOrEqual(4);

  // Top Lineups table renders rows from mock data
  await expect(page.getByText(/Tatum.*Brown/)).toBeVisible();

  // Run button present
  await expect(page.getByRole('button', { name: /Run Model/i })).toBeEnabled();
});
