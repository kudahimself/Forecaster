import { expect, test } from '@playwright/test'

test.describe('Features / DQ / Ingest pages', () => {
  test('feature importance page renders table with bars', async ({ page }) => {
    await page.goto('/features')
    await expect(page.getByRole('heading', { name: 'Feature importance' })).toBeVisible()
    const rows = page.locator('table.runs tbody tr')
    await expect(rows.first()).toBeVisible()
    // Inline bar gauge on each row
    await expect(rows.first().locator('div').filter({ hasText: '' }).last()).toBeVisible()
  })

  test('DQ dashboard shows latest-run stat grid', async ({ page }) => {
    await page.goto('/dq')
    await expect(page.getByRole('heading', { name: 'Data quality' })).toBeVisible()
    // Either has runs → stat-grid visible, or empty state
    const hasRuns = (await page.locator('.stat-grid').count()) > 0
    if (hasRuns) {
      await expect(page.locator('.stat', { hasText: 'pass' })).toBeVisible()
      await expect(page.locator('.stat', { hasText: 'warn' })).toBeVisible()
      await expect(page.locator('.stat', { hasText: 'fail' })).toBeVisible()
    } else {
      await expect(page.getByText('No DQ runs yet')).toBeVisible()
    }
  })

  test('ingest page shows freshness stats', async ({ page }) => {
    await page.goto('/ingest')
    await expect(page.getByRole('heading', { name: 'Ingest' })).toBeVisible()
    // stat grid should render price rows count
    await expect(page.locator('.stat', { hasText: /price rows/i })).toBeVisible()
    await expect(page.locator('.stat', { hasText: /symbols ingested/i })).toBeVisible()
  })

  test('sidebar navigation works', async ({ page }) => {
    await page.goto('/')
    await page.locator('.sidebar a').filter({ hasText: 'Features' }).click()
    await expect(page).toHaveURL('/features')
    await page.locator('.sidebar a').filter({ hasText: 'Data quality' }).click()
    await expect(page).toHaveURL('/dq')
    await page.locator('.sidebar a').filter({ hasText: 'Ingest' }).click()
    await expect(page).toHaveURL('/ingest')
    await page.locator('.sidebar a').filter({ hasText: 'Runs' }).click()
    await expect(page).toHaveURL('/')
  })
})
