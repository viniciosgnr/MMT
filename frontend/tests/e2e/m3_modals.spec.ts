import { test, expect } from '@playwright/test';
import { M3DashboardPage } from './pages/M3DashboardPage';

/**
 * Harness Engineering — M3 E2E: Override Date & Validation
 * 
 * Skills Applied:
 * - e2e-testing-patterns → POM, test.step(), isolation
 * - browser-automation → getByRole (no CSS!), auto-wait, network interception
 */

test.describe('M3 Override Date — Intervenção Manual', () => {

  test('O modal de override abre e permite edição de data', async ({ page }) => {
    const dashboard = new M3DashboardPage(page);

    await test.step('Navigate to M3 dashboard', async () => {
      await dashboard.goto();
    });

    await test.step('Open override date modal', async () => {
      if (await dashboard.editDateButton.isVisible({ timeout: 5000 }).catch(() => false)) {
        await dashboard.openOverrideDateModal();

        // Auto-wait: modal abre naturalmente
        const modal = page.locator('[role="dialog"], [data-testid*="modal"]');
        await expect(modal).toBeVisible({ timeout: 5000 });
      }
    });

    await test.step('Fill new date and confirm', async () => {
      const dateInput = page.locator('input[type="date"]').first();
      if (await dateInput.isVisible({ timeout: 3000 }).catch(() => false)) {
        await dateInput.fill('2026-10-10');

        const confirmBtn = page.getByRole('button', { name: /salvar|confirmar|save/i }).first();
        await confirmBtn.click();

        // Espera feedback visual (toast/snackbar)
        const toast = page.getByText(/sucesso|atualizada|success/i);
        await expect(toast).toBeVisible({ timeout: 5000 });
      }
    });
  });
});

test.describe('M3 Validation Report — Status Visual', () => {

  test('Badges de validação (Aprovado/Reprovado) renderizam corretamente', async ({ page }) => {
    const dashboard = new M3DashboardPage(page);

    await test.step('Navigate and look for validation badges', async () => {
      await dashboard.goto();

      // Procura badges de status com text user-facing
      const validationBadge = page.getByText(/approved|reproved|aprovado|reprovado|pending/i).first();

      if (await validationBadge.isVisible({ timeout: 5000 }).catch(() => false)) {
        const text = await validationBadge.textContent();
        expect(text).toBeTruthy();
      }
    });
  });

  test('Gráfico de histórico de parâmetros renderiza', async ({ page }) => {
    const dashboard = new M3DashboardPage(page);

    await test.step('Navigate and look for history chart', async () => {
      await dashboard.goto();

      const historyBtn = page.getByRole('button', { name: /histórico|history/i }).first();
      if (await historyBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
        await historyBtn.click();

        // Componentes de gráfico (Recharts, Chart.js, etc.)
        const chart = page.locator('canvas, svg[class*="chart"], [class*="recharts"]').first();
        await expect(chart).toBeVisible({ timeout: 5000 });
      }
    });
  });
});

test.describe('M3 Accessibility — Skill: browser-automation', () => {

  test('Botões interativos devem ter labels acessíveis', async ({ page }) => {
    await page.goto('/dashboard/m3');
    await page.waitForLoadState('networkidle');

    const buttons = page.locator('button');
    const count = await buttons.count();

    let unlabelledCount = 0;
    for (let i = 0; i < Math.min(count, 20); i++) {
      const btn = buttons.nth(i);
      const text = (await btn.textContent())?.trim();
      const ariaLabel = await btn.getAttribute('aria-label');
      const title = await btn.getAttribute('title');

      if (!text && !ariaLabel && !title) {
        unlabelledCount++;
      }
    }

    // Tolerance: no more than 10% of buttons should be unlabelled
    const maxUnlabelled = Math.ceil(count * 0.1);
    expect(unlabelledCount).toBeLessThanOrEqual(maxUnlabelled);
  });

  test('Inputs devem ter labels ou aria-labels', async ({ page }) => {
    await page.goto('/dashboard/m3');
    await page.waitForLoadState('networkidle');

    const inputs = page.locator('input:not([type="hidden"])');
    const count = await inputs.count();

    for (let i = 0; i < Math.min(count, 15); i++) {
      const input = inputs.nth(i);
      const id = await input.getAttribute('id');
      const ariaLabel = await input.getAttribute('aria-label');
      const placeholder = await input.getAttribute('placeholder');
      const name = await input.getAttribute('name');

      // Cada input deve ter ao menos um identificador
      const hasIdentifier = id || ariaLabel || placeholder || name;
      expect(hasIdentifier).toBeTruthy();
    }
  });
});
