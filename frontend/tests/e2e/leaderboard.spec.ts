import { expect, test } from '@playwright/test'

test.describe('Leaderboard', () => {
  test('renders the runs page with sidebar and table', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByRole('heading', { name: 'Runs', exact: true })).toBeVisible()
    await expect(page.locator('.sidebar')).toBeVisible()
    await expect(page.locator('.sidebar a').filter({ hasText: 'Runs' })).toBeVisible()
    await expect(page.locator('.sidebar a').filter({ hasText: 'Features' })).toBeVisible()
  })

  test('displays at least one run row', async ({ page }) => {
    await page.goto('/')
    const firstRow = page.locator('table.runs tbody tr').first()
    await expect(firstRow).toBeVisible()
  })

  test('clicking a run_id navigates to run detail', async ({ page }) => {
    await page.goto('/')
    const firstLink = page.locator('table.runs tbody tr:first-child a.id')
    const idText = (await firstLink.innerText()).trim()
    await firstLink.click()
    await expect(page).toHaveURL(/\/runs\//)
    // The run_id shortened label in the header should contain the same prefix.
    await expect(page.locator('.page-title')).toContainText(idText)
  })

  test('filter narrows results', async ({ page }) => {
    await page.goto('/')
    // Wait for at least one row to render before we start.
    await expect(page.locator('table.runs tbody tr').first()).toBeVisible()
    const before = await page.locator('table.runs tbody tr').count()

    const input = page.getByPlaceholder(/filter by/i)
    await input.click()
    await input.pressSequentially('__nonexistent_filter_string__', { delay: 10 })
    // Count-note reflects filtered count; easier to assert on than row count.
    await expect(page.locator('.count-note')).toContainText(/0 of \d+/)

    await input.fill('')
    await expect(page.locator('table.runs tbody tr')).toHaveCount(before)
  })

  test('sort toggles arrow indicator', async ({ page }) => {
    await page.goto('/')
    const header = page.locator('table.runs thead th', { hasText: /^cum_return/ })
    await header.click()
    await expect(header).toHaveClass(/sorted/)
  })

  test('compare button enables after two selections', async ({ page }) => {
    await page.goto('/')
    const compareBtn = page.getByRole('button', { name: /Compare/ })
    await expect(compareBtn).toBeDisabled()
    const checkboxes = page.locator('table.runs tbody tr input[type="checkbox"]')
    const count = await checkboxes.count()
    if (count >= 2) {
      await checkboxes.nth(0).check()
      await checkboxes.nth(1).check()
      await expect(compareBtn).toBeEnabled()
      await expect(compareBtn).toContainText('(2)')
    }
  })
})
