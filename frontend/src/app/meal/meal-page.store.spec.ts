import { TestBed } from '@angular/core/testing';
import { Subject } from 'rxjs';

import { ApiError, MealApiService } from './meal-api.service';
import { MealPageStore } from './meal-page.store';
import { MEAL } from './meal.fixtures';
import { AnalyzeResponse } from './meal.models';

describe('MealPageStore', () => {
  let store: MealPageStore;
  let response: Subject<AnalyzeResponse>;
  const analyze = vi.fn();

  beforeEach(() => {
    analyze.mockReset();
    analyze.mockImplementation(() => (response = new Subject()));
    TestBed.configureTestingModule({
      providers: [{ provide: MealApiService, useValue: { analyze } }],
    });
    store = TestBed.inject(MealPageStore);
  });

  function succeed(r = MEAL) {
    response.next(r);
    response.complete();
  }

  it('is busy only while a request runs', () => {
    store.submit(MEAL.text);
    expect(store.busy()).toBe(true);
    succeed();
    expect(store.busy()).toBe(false);
    expect(store.result()).toEqual(MEAL);
  });

  it('keeps the old result during a new request, then replaces it', () => {
    store.submit(MEAL.text);
    succeed();
    store.submit('2 eggs');
    expect(store.result()).toEqual(MEAL);
    succeed({ ...MEAL, text: '2 eggs' });
    expect(store.result()?.text).toBe('2 eggs');
  });

  it('clears the old result and shows the error when a request fails', () => {
    store.submit(MEAL.text);
    succeed();
    store.submit('hello');
    response.error(new ApiError('NO_FOOD_FOUND', 'No food.'));
    expect(store.result()).toBeNull();
    expect(store.error()?.code).toBe('NO_FOOD_FOUND');
    expect(store.busy()).toBe(false);
  });

  it('clears the error when a new request starts', () => {
    store.submit('hello');
    response.error(new ApiError('NETWORK', 'Offline.'));
    store.submit(MEAL.text);
    expect(store.error()).toBeNull();
  });

  it('retries with the last submitted text', () => {
    store.submit(MEAL.text);
    response.error(new ApiError('THROTTLED', 'Busy.'));
    store.retry();
    expect(analyze).toHaveBeenCalledTimes(2);
    expect(analyze).toHaveBeenLastCalledWith(MEAL.text);
  });

  it('ignores a submit while busy', () => {
    store.submit(MEAL.text);
    store.submit('2 eggs');
    expect(analyze).toHaveBeenCalledTimes(1);
  });

  it('is stale only when the draft differs from the analyzed text', () => {
    store.submit(MEAL.text);
    succeed();
    store.draft.set(`  ${MEAL.text} `);
    expect(store.stale()).toBe(false);
    store.draft.set('2 potatoes with gravy');
    expect(store.stale()).toBe(true);
  });
});
