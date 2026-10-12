import { TestBed } from '@angular/core/testing';

import { MEAL, STATED_ITEM } from '../meal.fixtures';
import { AnalyzeResponse } from '../meal.models';
import { MealResultComponent } from './meal-result';

async function render(result: AnalyzeResponse): Promise<HTMLElement> {
  const fixture = TestBed.createComponent(MealResultComponent);
  fixture.componentRef.setInput('result', result);
  await fixture.whenStable();
  return fixture.nativeElement;
}

describe('MealResultComponent', () => {
  it('summarizes how many amounts were estimated', async () => {
    const el = await render(MEAL);
    expect(el.querySelector('.summary')?.textContent).toContain('2 of 2 amounts were estimated');
  });

  it('puts each warning on its own food card', async () => {
    const el = await render(MEAL);
    const cards = el.querySelectorAll('app-food-item-card');
    expect(cards.length).toBe(2);
    expect(cards[0].textContent).toContain('202 g of mashed russet potato');
    expect(cards[0].textContent).not.toContain('60 g of gravy');
    expect(cards[1].textContent).toContain('60 g of gravy');
  });

  it('shows meal-level warnings above the foods', async () => {
    const el = await render({
      ...MEAL,
      warnings: [{ code: 'ENERGY_MISMATCH', message: 'Whole meal check.', item_index: null }],
    });
    const topLevel = el.querySelectorAll(':scope > app-warning-line');
    expect([...topLevel].map((w) => w.textContent)).toContainEqual(
      expect.stringContaining('Whole meal check.'),
    );
  });

  it('has no estimate summary when every amount was stated', async () => {
    const el = await render({ ...MEAL, items: [STATED_ITEM], warnings: [] });
    expect(el.querySelector('.summary')).toBeNull();
  });
});
