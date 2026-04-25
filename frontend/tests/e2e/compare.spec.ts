import { expect, test } from '@playwright/test'

test.describe('Compare', () => {
  test('empty state with no runs query param', async ({ page }) => {
    await page.goto('/compare')
    await expect(page.getByRole('heading', { name: /Compare runs/ })).toBeVisible()
    await expect(page.getByText('No runs selected')).toBeVisible()
  })

  test('compare button on leaderboard navigates to compare with 2 runs', async ({ page }) => {
    await page.goto('/')
    // Wait for at least 2 rows to render before we interact.
    await expect(page.locator('table.runs tbody tr').nth(1)).toBeVisible()

    const checkboxes = page.locator('table.runs tbody tr input[type="checkbox"]')
    await checkboxes.nth(0).check()
    await checkboxes.nth(1).check()
    await page.getByRole('button', { name: /Compare/ }).click()

    await expect(page).toHaveURL(/\/compare\?runs=/)
    await expect(page.getByRole('heading', { name: /Comparing 2 runs/ })).toBeVisible()

    // Both run chips with colour swatches appear
    await expect(page.locator('.pill .swatch').first()).toBeVisible()

    // Params + Metrics card-titles exist (scope to the uppercase labels)
    await expect(page.locator('.card-title', { hasText: /^Params\b/ }).first()).toBeVisible()
    await expect(page.locator('.card-title', { hasText: /^Metrics\b/ }).first()).toBeVisible()
  })
})
