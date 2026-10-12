import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { App } from './app';
import { MealApiService } from './meal/meal-api.service';

describe('App', () => {
  const analyze = vi.fn();

  beforeEach(() => {
    analyze.mockReset();
    TestBed.configureTestingModule({
      providers: [{ provide: MealApiService, useValue: { analyze } }],
    });
  });

  it('renders the meal input', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    expect(fixture.nativeElement.querySelector('app-meal-input')).toBeTruthy();
  });

  it('sends the submitted text to the API', async () => {
    analyze.mockReturnValue(of({}));
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const el: HTMLElement = fixture.nativeElement;

    const textarea = el.querySelector('textarea')!;
    textarea.value = '2 eggs';
    textarea.dispatchEvent(new Event('input'));
    await fixture.whenStable();
    [...el.querySelectorAll('button')].find((b) => b.textContent?.includes('Calculate'))!.click();

    expect(analyze).toHaveBeenCalledWith('2 eggs');
  });
});
