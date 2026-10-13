// Keeps the description and the last result in sessionStorage, so a refresh
// shows the same page. sessionStorage belongs to one tab and is cleared when the
// tab closes; nothing here leaves the browser.

import { validateAnalyzeResponse } from './meal-validation';
import { AnalyzeResponse } from './meal.models';

// Bump the version if the saved shape changes, so old saves are ignored.
export const STORAGE_KEY = 'words2macros:last-meal:v1';

export interface SavedMeal {
  draft: string; // what was in the description box
  result: AnalyzeResponse | null; // the last successful result
}

const EMPTY: SavedMeal = { draft: '', result: null };

/** Null when the browser blocks storage (some private windows do). */
function storage(): Storage | null {
  try {
    return window.sessionStorage;
  } catch {
    return null;
  }
}

/**
 * The saved meal, or an empty one. Saved data is checked like an API response:
 * it may come from an older version of the app, or have been edited by hand.
 */
export function loadMeal(): SavedMeal {
  try {
    const raw = storage()?.getItem(STORAGE_KEY);
    if (!raw) return EMPTY;
    const saved = JSON.parse(raw);
    const draft = typeof saved?.draft === 'string' ? saved.draft : '';
    let result: AnalyzeResponse | null = null;
    try {
      result = saved?.result ? validateAnalyzeResponse(saved.result) : null;
    } catch {
      // Not a valid result any more; keep the draft, drop the result.
    }
    return { draft, result };
  } catch {
    return EMPTY; // unreadable JSON or blocked storage
  }
}

export function saveMeal(meal: SavedMeal): void {
  try {
    storage()?.setItem(STORAGE_KEY, JSON.stringify(meal));
  } catch {
    // Storage full or blocked: the page still works, it just won't survive a refresh.
  }
}
