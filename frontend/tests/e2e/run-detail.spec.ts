import { expect, test } from '@playwright/test'

test.describe('Run detail', () => {
  test('clicks first run and shows stat grid + equity curve', async ({ page }) => {
    await page.goto('/')
    await page.locator('table.runs tbody tr:first-child a.id').click()

    // Header & stat grid
    await expect(page.locator('.stat-grid')).toBeVisible()
    await expect(page.locator('.stat', { hasText: 'experiment' })).toBeVisible()
    await expect(page.locator('.stat', { hasText: 'started' })).toBeVisible()

    // Equity curve heading
    await expect(page.getByText('Cumulative portfolio return')).toBeVisible()

    // Either the recharts SVG renders (have portfolio returns) or the empty-state
    // message shows — both are acceptable. Chart render takes a tick.
    const chart = page.locator('.chart-card svg, .chart-card .empty-state, .chart-card [class*="empty"]')
    await expect(chart.first()).toBeVisible()
  })

  test('params and metrics tables are populated', async ({ page }) => {
    await page.goto('/')
    await page.locator('table.runs tbody tr:first-child a.id').click()

    // Params grid: look for well-known key "top_k"
    await expect(page.locator('.kv-grid .k', { hasText: 'top_k' }).first()).toBeVisible()

    // Metrics grid: at least one metric key
    await expect(page.locator('.kv-grid .k', { hasText: 'n_rebalance_dates' }).first()).toBeVisible()
  })

  test('back-button returns to leaderboard', async ({ page }) => {
    await page.goto('/')
    await page.locator('table.runs tbody tr:first-child a.id').click()
    await page.getByRole('link', { name: /All runs/ }).click()
    await expect(page).toHaveURL('/')
    await expect(page.getByRole('heading', { name: 'Runs', exact: true })).toBeVisible()
  })
})
