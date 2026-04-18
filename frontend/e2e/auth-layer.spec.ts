import { expect, test, type Page } from '@playwright/test'

const runFull = process.env.E2E_RUN_FULL === '1'
const userName = process.env.E2E_USER_USERNAME || 'zhangsan'
const userPassword = process.env.E2E_USER_PASSWORD || ''
const adminName = process.env.E2E_ADMIN_USERNAME || 'lisi'
const adminPassword = process.env.E2E_ADMIN_PASSWORD || ''

async function login(page: Page, username: string, password: string) {
  await page.getByLabel('用户名').fill(username)
  await page.getByLabel('密码').fill(password)
  await page.getByRole('button', { name: '登录' }).click()
}

test.describe('Auth Layer E2E (3 roles)', () => {
  test.beforeEach(async () => {
    test.skip(!runFull, 'Set E2E_RUN_FULL=1 and provide credentials to run full e2e matrix.')
  })

  test('匿名用户可浏览，申报触发登录', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByText('HEBEI · AI 应用广场')).toBeVisible()
    await expect(page.getByRole('button', { name: '管理员登录' })).toBeVisible()
    await expect(page.getByRole('button', { name: '我要申报' })).toBeVisible()
    await expect(page.getByText('我的申报')).toHaveCount(0)

    await page.getByRole('button', { name: '我要申报' }).click()
    await expect(page).toHaveURL(/\/login$/)
  })

  test('登录用户可申报且不可访问管理页', async ({ page }) => {
    test.skip(!userPassword, 'Set E2E_USER_PASSWORD to run user flow.')
    await page.goto('/login')
    await login(page, userName, userPassword)
    await expect(page).toHaveURL(/\/$/)

    await page.getByRole('button', { name: '我要申报' }).click()
    await expect(page.getByText('应用申报')).toBeVisible()
    await page.getByRole('button', { name: '取消' }).click()

    await page.goto('/my-submissions')
    await expect(page.getByText('我的申报')).toBeVisible()

    await page.goto('/ranking-management')
    await expect(page.getByText('当前账号不是管理员，无法访问管理功能。')).toBeVisible()
  })

  test('管理员可访问管理路由', async ({ page }) => {
    test.skip(!adminPassword, 'Set E2E_ADMIN_PASSWORD to run admin flow.')
    await page.goto('/login')
    await login(page, adminName, adminPassword)
    await expect(page).toHaveURL(/\/$/)

    await page.goto('/ranking-management')
    await expect(page).toHaveURL(/\/ranking-management$/)
  })
})
