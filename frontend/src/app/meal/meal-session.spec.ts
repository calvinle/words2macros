import { MEAL } from './meal.fixtures';
import { STORAGE_KEY, loadMeal, saveMeal } from './meal-session';

describe('meal session storage', () => {
  beforeEach(() => sessionStorage.clear());
  afterEach(() => vi.restoreAllMocks());

  it('starts empty', () => {
    expect(loadMeal()).toEqual({ draft: '', result: null });
  });

  it('round-trips the draft and the result', () => {
    saveMeal({ draft: '2 eggs', result: MEAL });
    expect(loadMeal()).toEqual({ draft: '2 eggs', result: MEAL });
  });

  it('drops a saved result that no longer validates, keeping the draft', () => {
    // e.g. saved by a version of the app from before fiber was added
    const { fiber_g, ...oldTotals } = MEAL.totals;
    const old = { ...MEAL, totals: oldTotals };
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ draft: '2 eggs', result: old }));

    expect(loadMeal()).toEqual({ draft: '2 eggs', result: null });
  });

  it('ignores unreadable data', () => {
    sessionStorage.setItem(STORAGE_KEY, '{not json');
    expect(loadMeal()).toEqual({ draft: '', result: null });
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ draft: 42 }));
    expect(loadMeal()).toEqual({ draft: '', result: null });
  });

  it('keeps working when storage is blocked or full', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new DOMException('blocked', 'SecurityError');
    });
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new DOMException('full', 'QuotaExceededError');
    });

    expect(() => saveMeal({ draft: '2 eggs', result: MEAL })).not.toThrow();
    expect(loadMeal()).toEqual({ draft: '', result: null });
  });
});
