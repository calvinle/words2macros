import { TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';

import { App } from './app';
import { ApiError, MealApiService } from './meal/meal-api.service';

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

  it('focuses the description when an error asks to edit it', async () => {
    analyze.mockReturnValue(throwError(() => new ApiError('NO_FOOD_FOUND', 'No food found.')));
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const el: HTMLElement = fixture.nativeElement;
    document.body.appendChild(el); // focus only works on attached elements

    const textarea = el.querySelector('textarea')!;
    textarea.value = 'hello';
    textarea.dispatchEvent(new Event('input'));
    await fixture.whenStable();
    [...el.querySelectorAll('button')].find((b) => b.textContent?.includes('Calculate'))!.click();
    await fixture.whenStable();

    const edit = [...el.querySelectorAll('app-error-panel button')][0] as HTMLButtonElement;
    expect(edit.textContent).toContain('Edit description');
    edit.click();
    expect(document.activeElement).toBe(textarea);
    el.remove();
  });
});
