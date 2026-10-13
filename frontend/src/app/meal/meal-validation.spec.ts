import { AI_ESTIMATED_ITEM, MEAL, TEQUILA_ITEM } from './meal.fixtures';
import { ValidationError, validateAnalyzeResponse } from './meal-validation';

/** A deep copy of MEAL with one change applied. */
function mealWith(change: (m: any) => void): unknown {
  const copy = structuredClone(MEAL);
  change(copy);
  return copy;
}

describe('validateAnalyzeResponse', () => {
  it('accepts real responses unchanged', () => {
    expect(validateAnalyzeResponse(MEAL)).toBe(MEAL);
    const others = { ...MEAL, items: [AI_ESTIMATED_ITEM, TEQUILA_ITEM], warnings: [] };
    expect(validateAnalyzeResponse(others)).toBe(others);
  });

  it('accepts unreported fiber as null', () => {
    const r = mealWith((m) => (m.items[1].nutrients.fiber_g = null));
    expect(() => validateAnalyzeResponse(r)).not.toThrow();
  });

  it('accepts fiber equal to carbs', () => {
    const r = mealWith((m) => (m.totals.fiber_g = m.totals.carbs_g));
    expect(() => validateAnalyzeResponse(r)).not.toThrow();
  });

  it.each([
    [
      'fiber over carbs',
      (m: any) => (m.items[0].nutrients.fiber_g = 99),
      'items[0].nutrients.fiber_g',
    ],
    ['negative fiber', (m: any) => (m.totals.fiber_g = -1), 'totals.fiber_g'],
    ['missing fiber', (m: any) => delete m.items[0].match.per_100g.fiber_g, 'per_100g.fiber_g'],
    ['fiber as text', (m: any) => (m.totals.fiber_g = '2'), 'totals.fiber_g'],
    ['missing calories', (m: any) => delete m.totals.calories_kcal, 'totals.calories_kcal'],
    ['negative fat', (m: any) => (m.items[1].nutrients.fat_g = -0.1), 'items[1].nutrients.fat_g'],
    ['zero grams', (m: any) => (m.items[0].grams = 0), 'items[0].grams'],
    ['bad amount source', (m: any) => (m.items[0].amount_source = 'guessed'), 'amount_source'],
    ['missing dry flag', (m: any) => delete m.items[0].dry_amount, 'items[0].dry_amount'],
    ['estimate without assumption', (m: any) => (m.items[0].assumption = null), 'assumption'],
    ['USDA match without ID', (m: any) => (m.items[0].match.fdc_id = null), 'match.fdc_id'],
    ['unknown warning code', (m: any) => (m.warnings[0].code = 'NEW_CODE'), 'warnings[0].code'],
    ['no foods', (m: any) => (m.items = []), 'items'],
    ['no request ID', (m: any) => delete m.request_id, 'request_id'],
  ])('rejects %s', (_, change, path) => {
    expect(() => validateAnalyzeResponse(mealWith(change))).toThrow(ValidationError);
    expect(() => validateAnalyzeResponse(mealWith(change))).toThrow(path);
  });

  it('rejects something that is not a response', () => {
    expect(() => validateAnalyzeResponse(null)).toThrow(ValidationError);
    expect(() => validateAnalyzeResponse('<html>')).toThrow(ValidationError);
  });
});
