// Mirrors src/words2macros/models.py. Keep the two in sync.
// meal-validation.ts checks responses against these shapes at runtime.

export const MAX_INPUT_CHARS = 2000; // parse.py
export const MAX_ITEMS_PER_MEAL = 15; // models.py

export type AmountSource = 'stated' | 'estimated';
export type MatchSource = 'usda' | 'ai_estimate';

export const WARNING_CODES = [
  'AMOUNT_ESTIMATED', // the AI guessed a portion size
  'CALORIE_DENSE_ESTIMATE', // guessed portion of a calorie-dense food
  'NUTRIENTS_ESTIMATED', // no database match; nutrients are an AI estimate
  'ENERGY_MISMATCH', // calories far from 4P + 4C + 9F + 7A, likely a bad match
  'OVER_2000G', // implausibly large single item
  'FIBER_NOT_REPORTED', // the record has no fiber value; left out of the total
] as const;
export type WarningCode = (typeof WARNING_CODES)[number];

export interface Nutrients {
  calories_kcal: number;
  protein_g: number;
  carbs_g: number; // includes fiber
  fat_g: number;
  alcohol_g: number; // 0 for most foods
  fiber_g: number | null; // null when the source doesn't report it; never more than carbs_g
}

export interface FoodMatch {
  source: MatchSource;
  fdc_id: number | null;
  description: string;
  per_100g: Nutrients;
}

export interface ItemResult {
  name: string;
  preparation: string | null;
  grams: number;
  amount_source: AmountSource;
  assumption: string | null;
  match: FoodMatch;
  nutrients: Nutrients;
}

export interface MealWarning {
  code: WarningCode;
  message: string;
  item_index: number | null; // null for meal-level warnings
}

/** The POST /analyze success body. */
export interface AnalyzeResponse {
  items: ItemResult[];
  totals: Nutrients;
  warnings: MealWarning[];
  text: string; // the original input, echoed back
  request_id: string;
  analyzed_at: string; // ISO 8601, UTC
}
