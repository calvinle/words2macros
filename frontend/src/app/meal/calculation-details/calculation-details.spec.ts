import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AI_ESTIMATED_ITEM, MEAL } from '../meal.fixtures';
import { AnalyzeResponse } from '../meal.models';
import { CalculationDetailsComponent } from './calculation-details';

describe('CalculationDetailsComponent', () => {
  let fixture: ComponentFixture<CalculationDetailsComponent>;

  async function render(result: AnalyzeResponse): Promise<HTMLElement> {
    fixture = TestBed.createComponent(CalculationDetailsComponent);
    fixture.componentRef.setInput('result', result);
    await fixture.whenStable();
    return fixture.nativeElement;
  }

  async function open(el: HTMLElement): Promise<HTMLElement> {
    el.querySelector<HTMLElement>('mat-expansion-panel-header')!.click();
    await fixture.whenStable();
    return el;
  }

  it('is collapsed, with the steps not built until opened', async () => {
    const el = await render(MEAL);
    expect(el.textContent).toContain('How this was calculated');
    expect(el.querySelector('.steps')).toBeNull();
    await open(el);
    expect(el.querySelectorAll('.steps > li').length).toBe(4);
  });

  it('shows the calculation with the backend result', async () => {
    const el = await open(await render(MEAL));
    const math = [...el.querySelectorAll('.math')].map((m) => m.textContent?.replace(/\s+/g, ' '));
    expect(math[0]).toContain('202 g × 114 kcal / 100 g = 230.3 kcal');
    expect(el.querySelector('.total')?.textContent).toContain('262.1 kcal');
  });

  it("takes each check's verdict from the backend warnings", async () => {
    const mismatch = {
      ...MEAL,
      warnings: [
        ...MEAL.warnings,
        { code: 'ENERGY_MISMATCH' as const, message: 'Check match.', item_index: 1 },
      ],
    };
    const el = await open(await render(mismatch));
    const foods = [...el.querySelectorAll('.steps > li:nth-child(4) .food')];
    expect(foods[0].textContent).toContain('Calories add up from the macros');
    expect(foods[1].textContent).toContain("Calories don't add up from the macros");
    expect(foods[0].textContent).toContain('Amount estimated');
  });

  it('shows the energy calculation behind the check', async () => {
    const el = await open(await render(MEAL));
    // Potato per 100 g: 4×2.15 + 4×17.6 + 9×4.07 = 115.63
    expect(el.querySelector('.detail')?.textContent?.replace(/\s+/g, ' ')).toContain(
      '= 116 kcal vs 114 listed',
    );
  });

  it('labels an AI-estimated match', async () => {
    const el = await open(await render({ ...MEAL, items: [AI_ESTIMATED_ITEM], warnings: [] }));
    expect(el.textContent).toContain('AI estimate (no USDA match)');
  });
});
