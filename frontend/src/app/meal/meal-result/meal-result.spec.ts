import { TestBed } from '@angular/core/testing';

import { MEAL, STATED_ITEM } from '../meal.fixtures';
import { AnalyzeResponse } from '../meal.models';
import { MealResultComponent } from './meal-result';

async function render(result: AnalyzeResponse, stale = false): Promise<HTMLElement> {
  const fixture = TestBed.createComponent(MealResultComponent);
  fixture.componentRef.setInput('result', result);
  fixture.componentRef.setInput('stale', stale);
  await fixture.whenStable();
  return fixture.nativeElement;
}

describe('MealResultComponent', () => {
  it('shows which text the result is for', async () => {
    const el = await render(MEAL);
    expect(el.querySelector('.results-for')?.textContent).toContain(MEAL.text);
  });

  it('says when the description has changed since the result', async () => {
    expect((await render(MEAL)).querySelector('.stale')).toBeNull();
    expect((await render(MEAL, true)).querySelector('.stale')?.textContent).toContain(
      'has changed since this result',
    );
  });

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
