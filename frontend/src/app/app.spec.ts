import { TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';

import { App } from './app';
import { ApiError, MealApiService } from './meal/meal-api.service';
import { saveMeal } from './meal/meal-session';
import { MEAL } from './meal/meal.fixtures';

describe('App', () => {
  const analyze = vi.fn();

  beforeEach(() => {
    sessionStorage.clear();
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

  describe('scrolling to results below the screen', () => {
    const scroll = vi.fn();

    beforeEach(() => {
      scroll.mockReset();
      Element.prototype.scrollIntoView = scroll; // jsdom has no scrolling
      vi.spyOn(Element.prototype, 'getBoundingClientRect').mockReturnValue({
        top: 5000,
      } as DOMRect);
    });

    afterEach(() => {
      delete (Element.prototype as Partial<Element>).scrollIntoView;
      vi.restoreAllMocks();
    });

    it('brings a new result into view', async () => {
      analyze.mockReturnValue(of(MEAL));
      const fixture = TestBed.createComponent(App);
      await fixture.whenStable();
      fixture.componentInstance['store'].submit(MEAL.text);
      await fixture.whenStable();

      expect(scroll).toHaveBeenCalled();
    });

    it('shows the saved description and result after a refresh, without scrolling', async () => {
      saveMeal({ draft: MEAL.text, result: MEAL });

      const fixture = TestBed.createComponent(App);
      await fixture.whenStable();
      const el: HTMLElement = fixture.nativeElement;

      expect(el.querySelector('textarea')!.value).toBe(MEAL.text);
      expect(el.querySelector('app-meal-result')?.textContent).toContain(MEAL.text);
      expect(scroll).not.toHaveBeenCalled(); // the user is already where they left off
      expect(analyze).not.toHaveBeenCalled();
    });
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
