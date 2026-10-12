// Test data. MEAL is a real /analyze response from 2026-10-11.

import { AnalyzeResponse, ItemResult } from './meal.models';

export const MEAL: AnalyzeResponse = {
  items: [
    {
      name: 'russet potato',
      preparation: 'mashed',
      grams: 202,
      amount_source: 'estimated',
      assumption: '1 medium russet potato',
      match: {
        source: 'usda',
        fdc_id: 2709492,
        description: 'Potato, mashed, NFS',
        per_100g: { calories_kcal: 114, protein_g: 2.15, carbs_g: 17.6, fat_g: 4.07 },
      },
      nutrients: { calories_kcal: 230.3, protein_g: 4.3, carbs_g: 35.6, fat_g: 8.2 },
    },
    {
      name: 'gravy',
      preparation: null,
      grams: 60,
      amount_source: 'estimated',
      assumption: '1 serving of gravy',
      match: {
        source: 'usda',
        fdc_id: 2707149,
        description: 'Gravy, NFS',
        per_100g: { calories_kcal: 53, protein_g: 3.75, carbs_g: 4.81, fat_g: 2.36 },
      },
      nutrients: { calories_kcal: 31.8, protein_g: 2.2, carbs_g: 2.9, fat_g: 1.4 },
    },
  ],
  totals: { calories_kcal: 262.1, protein_g: 6.6, carbs_g: 38.4, fat_g: 9.6 },
  warnings: [
    {
      code: 'AMOUNT_ESTIMATED',
      message:
        'An estimated 202 g of mashed russet potato was used (assumed: 1 medium russet potato). For more accurate results, enter a measured amount (grams, cups, etc.) and double check your input.',
      item_index: 0,
    },
    {
      code: 'AMOUNT_ESTIMATED',
      message:
        'An estimated 60 g of gravy was used (assumed: 1 serving of gravy). For more accurate results, enter a measured amount (grams, cups, etc.) and double check your input.',
      item_index: 1,
    },
  ],
  text: 'I had mashed potatoes from a medium russet potato with a serving of gravy.',
  request_id: '81ef40f8-f5ee-48c4-9406-209a26fd1eb1',
  analyzed_at: '2026-10-12T00:40:33.643663Z',
};

export const STATED_ITEM: ItemResult = {
  name: 'chicken breast',
  preparation: 'grilled',
  grams: 150,
  amount_source: 'stated',
  assumption: null,
  match: {
    source: 'usda',
    fdc_id: 171477,
    description: 'Chicken, broilers or fryers, breast, meat only, cooked, roasted',
    per_100g: { calories_kcal: 165, protein_g: 31, carbs_g: 0, fat_g: 3.6 },
  },
  nutrients: { calories_kcal: 247.5, protein_g: 46.5, carbs_g: 0, fat_g: 5.4 },
};

export const AI_ESTIMATED_ITEM: ItemResult = {
  ...STATED_ITEM,
  name: 'grandma special stew',
  preparation: null,
  match: {
    source: 'ai_estimate',
    fdc_id: null,
    description: 'Beef stew (AI estimate)',
    per_100g: { calories_kcal: 100, protein_g: 7, carbs_g: 8, fat_g: 4 },
  },
};
