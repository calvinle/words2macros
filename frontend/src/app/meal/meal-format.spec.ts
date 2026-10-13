import {
  energyFromMacros,
  estimatedCount,
  macroShares,
  mealLevelWarnings,
  warningsForItem,
} from './meal-format';
import { MEAL, STATED_ITEM } from './meal.fixtures';
import { MealWarning } from './meal.models';

const NONE = { calories_kcal: 0, protein_g: 0, carbs_g: 0, fat_g: 0, alcohol_g: 0, fiber_g: 0 };

describe('macroShares', () => {
  it('splits calories 4/4/9 and adds up to 100', () => {
    // 6.6 g P = 26.4, 38.4 g C = 153.6, 9.6 g F = 86.4 kcal; 266.4 in all
    expect(macroShares(MEAL.totals)).toEqual({ protein: 10, carbs: 58, fat: 32 });
  });

  it('adds up to 100 when every share rounds down', () => {
    const s = macroShares({ ...NONE, protein_g: 1, carbs_g: 1, fat_g: 4 / 9 })!;
    expect(s.protein + s.carbs + s.fat).toBe(100);
  });

  it('returns null when there are no macros', () => {
    expect(macroShares(NONE)).toBeNull();
  });
});

describe('warning grouping', () => {
  const mealWide: MealWarning = { code: 'ENERGY_MISMATCH', message: 'Meal.', item_index: null };
  const warnings = [...MEAL.warnings, mealWide];

  it('picks the warnings for one item', () => {
    expect(warningsForItem(warnings, 1)).toEqual([MEAL.warnings[1]]);
  });

  it('picks the meal-level warnings', () => {
    expect(mealLevelWarnings(warnings)).toEqual([mealWide]);
  });
});

describe('estimatedCount', () => {
  it('counts estimated amounts only', () => {
    expect(estimatedCount(MEAL.items)).toBe(2);
    expect(estimatedCount([STATED_ITEM])).toBe(0);
  });
});

describe('energyFromMacros', () => {
  it('uses 4/4/9/7 kcal per gram', () => {
    expect(energyFromMacros({ ...NONE, protein_g: 1, carbs_g: 1, fat_g: 1, alcohol_g: 1 })).toBe(
      24,
    );
  });
});
