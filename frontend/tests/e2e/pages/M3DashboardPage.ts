import { type Page, type Locator } from '@playwright/test';

/**
 * Page Object Model: M3 Dashboard (Kanban)
 * 
 * Skill Applied: e2e-testing-patterns → POM + Stable Selectors
 * Skill Applied: browser-automation → getByRole, getByText, getByTestId
 * 
 * Centraliza todos os locators do Kanban do M3 Chemical Analysis.
 * Se um redesign do frontend mudar nomes de classes, apenas este POM precisa ser atualizado.
 */
export class M3DashboardPage {
  readonly page: Page;

  // Kanban Column Headers
  readonly planSampleColumn: Locator;
  readonly disembarkColumn: Locator;
  readonly logisticsColumn: Locator;
  readonly validationColumn: Locator;
  readonly flowComputerColumn: Locator;

  // Action Buttons
  readonly uploadButton: Locator;
  readonly editDateButton: Locator;
  readonly addSampleButton: Locator;

  // Sample Cards
  readonly sampleCards: Locator;

  constructor(page: Page) {
    this.page = page;

    // User-facing locators — resilientes a mudanças de CSS
    this.planSampleColumn = page.getByText(/plan|sample/i).first();
    this.disembarkColumn = page.getByText(/disembark/i).first();
    this.logisticsColumn = page.getByText(/logistics|warehouse/i).first();
    this.validationColumn = page.getByText(/validation|report/i).first();
    this.flowComputerColumn = page.getByText(/flow computer|fc update/i).first();

    // Buttons via role (não CSS!)
    this.uploadButton = page.getByRole('button', { name: /upload/i });
    this.editDateButton = page.getByRole('button', { name: /edit|override|forçar/i }).first();
    this.addSampleButton = page.getByRole('button', { name: /add|nova|criar/i }).first();

    // Sample cards via testid ou fallback
    this.sampleCards = page.locator('[data-testid*="sample-card"], [class*="sample"], tr');
  }

  async goto() {
    await this.page.goto('/dashboard/m3');
  }

  async clickFirstSampleCard() {
    await this.sampleCards.first().click();
  }

  async openOverrideDateModal() {
    await this.editDateButton.click();
  }

  async setOverrideDate(dateStr: string) {
    const dateInput = this.page.locator('input[type="date"]').first();
    await dateInput.fill(dateStr);
    const confirmBtn = this.page.getByRole('button', { name: /salvar|confirmar|save/i }).first();
    await confirmBtn.click();
  }
}
