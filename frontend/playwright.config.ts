import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright Configuration — MMT Project
 * 
 * Configurado conforme as skills:
 * - e2e-testing-patterns: retries, trace capture, parallelism
 * - browser-automation: auto-wait, screenshot on failure, video on failure
 * 
 * @see {@link .agent/skills/e2e-testing-patterns/resources/implementation-playbook.md}
 * @see {@link .agent/skills/browser-automation/SKILL.md}
 */
export default defineConfig({
  testDir: './tests/e2e',
  timeout: 30000,
  expect: {
    timeout: 5000,
  },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html', { open: 'never' }],
    ['list'],
  ],
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:3000',
    // Skills mandate: trace + screenshot + video on failure for CI debugging
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'mobile',
      use: { ...devices['iPhone 13'] },
    },
  ],
});
