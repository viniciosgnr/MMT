import { type Page, type Locator } from '@playwright/test';

/**
 * Page Object Model: Login Page
 * 
 * Skill Applied: e2e-testing-patterns → Pattern 1: Page Object Model
 * Skill Applied: browser-automation → User-Facing Locator Pattern
 * 
 * Encapsula toda a interação com a tela de login do MMT.
 * Usa getByLabel/getByRole em vez de CSS selectors (anti-pattern).
 */
export class LoginPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly loginButton: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.getByLabel('Email');
    this.passwordInput = page.getByLabel('Password');
    this.loginButton = page.getByRole('button', { name: /entrar|login|sign in/i });
    this.errorMessage = page.getByRole('alert');
  }

  async goto() {
    await this.page.goto('/login');
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.loginButton.click();
  }
}
