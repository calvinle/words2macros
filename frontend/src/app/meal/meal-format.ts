// Display logic for meal results, kept out of components so it is easy to test.

import { ItemResult, MealWarning, Nutrients, WarningCode } from './meal.models';

export type Severity = 'info' | 'warning';

/** Estimated amounts are routine, so they stay calm; the rest need attention. */
export const WARNING_SEVERITY: Record<WarningCode, Severity> = {
  AMOUNT_ESTIMATED: 'info',
  CALORIE_DENSE_ESTIMATE: 'warning',
  NUTRIENTS_ESTIMATED: 'warning',
  ENERGY_MISMATCH: 'warning',
  OVER_2000G: 'warning',
};

/** Whole-number percentages of calories from each macro. */
export interface MacroShares {
  protein: number;
  carbs: number;
  fat: number;
}

/**
 * Share of calories from protein, carbs and fat (4, 4 and 9 kcal per gram).
 * Uses largest-remainder rounding so the three always add up to exactly 100.
 * Null when there are no macro calories to split.
 */
export function macroShares(n: Nutrients): MacroShares | null {
  const kcal = [n.protein_g * 4, n.carbs_g * 4, n.fat_g * 9];
  const total = kcal.reduce((a, b) => a + b, 0);
  if (total <= 0) return null;

  const exact = kcal.map((k) => (k / total) * 100);
  const shares = exact.map(Math.floor);
  const byRemainder = [0, 1, 2].sort((a, b) => exact[b] - shares[b] - (exact[a] - shares[a]));
  const missing = 100 - shares.reduce((a, b) => a + b, 0);
  for (let i = 0; i < missing; i++) {
    shares[byRemainder[i]]++;
  }
  return { protein: shares[0], carbs: shares[1], fat: shares[2] };
}

export function warningsForItem(warnings: MealWarning[], index: number): MealWarning[] {
  return warnings.filter((w) => w.item_index === index);
}

/** Warnings about the whole meal rather than one food. */
export function mealLevelWarnings(warnings: MealWarning[]): MealWarning[] {
  return warnings.filter((w) => w.item_index === null);
}

export function estimatedCount(items: ItemResult[]): number {
  return items.filter((i) => i.amount_source === 'estimated').length;
}
