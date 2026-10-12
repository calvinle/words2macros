import { TestBed } from '@angular/core/testing';

import { AI_ESTIMATED_ITEM, MEAL, STATED_ITEM } from '../meal.fixtures';
import { ItemResult, MealWarning } from '../meal.models';
import { FoodItemCardComponent } from './food-item-card';

async function render(item: ItemResult, warnings: MealWarning[] = []): Promise<HTMLElement> {
  const fixture = TestBed.createComponent(FoodItemCardComponent);
  fixture.componentRef.setInput('item', item);
  fixture.componentRef.setInput('warnings', warnings);
  await fixture.whenStable();
  return fixture.nativeElement;
}

describe('FoodItemCardComponent', () => {
  it('marks an estimated amount with a badge and ~', async () => {
    const el = await render(MEAL.items[0]);
    expect(el.querySelector('.badge')?.textContent).toContain('Estimated');
    expect(el.querySelector('.grams')?.textContent).toContain('~202 g');
  });

  it('shows a stated amount without ~', async () => {
    const el = await render(STATED_ITEM);
    expect(el.querySelector('.badge')?.textContent).toContain('Stated');
    expect(el.querySelector('.grams')?.textContent?.trim()).toBe('150 g');
  });

  it('shows its warnings, styled by severity', async () => {
    const amber: MealWarning = { code: 'ENERGY_MISMATCH', message: 'Check match.', item_index: 0 };
    const el = await render(MEAL.items[0], [MEAL.warnings[0], amber]);
    const lines = el.querySelectorAll('app-warning-line');
    expect(lines.length).toBe(2);
    expect(lines[0].textContent).toContain('An estimated 202 g');
    expect(lines[0].classList).not.toContain('warning');
    expect(lines[1].classList).toContain('warning');
  });

  it('shows the USDA record used', async () => {
    const el = await render(MEAL.items[0]);
    expect(el.querySelector('.match')?.textContent).toContain(
      'USDA match: Potato, mashed, NFS (FDC 2709492)',
    );
  });

  it('labels nutrients that came from an AI estimate', async () => {
    const el = await render(AI_ESTIMATED_ITEM);
    expect(el.querySelector('.match')?.textContent).toContain('AI estimate (no USDA match)');
  });
});
