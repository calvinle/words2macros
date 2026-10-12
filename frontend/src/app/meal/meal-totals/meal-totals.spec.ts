import { TestBed } from '@angular/core/testing';

import { MEAL } from '../meal.fixtures';
import { MealTotalsComponent } from './meal-totals';

async function render(estimated: boolean, totals = MEAL.totals): Promise<HTMLElement> {
  const fixture = TestBed.createComponent(MealTotalsComponent);
  fixture.componentRef.setInput('totals', totals);
  fixture.componentRef.setInput('estimated', estimated);
  await fixture.whenStable();
  return fixture.nativeElement;
}

describe('MealTotalsComponent', () => {
  it('marks estimated totals with ~ and a note', async () => {
    const el = await render(true);
    expect(el.querySelector('.calories')?.textContent).toContain('~262');
    expect(el.textContent).toContain('Includes estimated amounts');
  });

  it('shows exact totals without ~', async () => {
    const el = await render(false);
    expect(el.querySelector('.calories')?.textContent).not.toContain('~');
    expect(el.textContent).not.toContain('Includes estimated amounts');
  });

  it('shows alcohol only when there is some', async () => {
    expect((await render(false)).textContent).not.toContain('Alcohol');
    const withDrink = await render(false, { ...MEAL.totals, alcohol_g: 15 });
    expect(withDrink.querySelector('.macros')?.textContent).toContain('Alcohol15.0 g');
  });

  it('describes the macro split for screen readers', async () => {
    const el = await render(false);
    expect(el.querySelector('.bar')?.getAttribute('aria-label')).toBe(
      'Calories from protein 10%, carbs 58%, fat 32%',
    );
  });
});
