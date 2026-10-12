import { TestBed } from '@angular/core/testing';

import { MEAL } from '../meal.fixtures';
import { MealTotalsComponent } from './meal-totals';

async function render(estimated: boolean): Promise<HTMLElement> {
  const fixture = TestBed.createComponent(MealTotalsComponent);
  fixture.componentRef.setInput('totals', MEAL.totals);
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

  it('describes the macro split for screen readers', async () => {
    const el = await render(false);
    expect(el.querySelector('.bar')?.getAttribute('aria-label')).toBe(
      'Calories from protein 10%, carbs 58%, fat 32%',
    );
  });
});
