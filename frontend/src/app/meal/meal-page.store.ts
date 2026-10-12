import { Injectable, computed, inject, signal } from '@angular/core';

import { ApiError, MealApiService } from './meal-api.service';
import { AnalyzeResponse } from './meal.models';

/** State for the meal page: the current request, its result or error, and the draft text. */
@Injectable({ providedIn: 'root' })
export class MealPageStore {
  private readonly api = inject(MealApiService);
  private lastText: string | null = null;

  readonly busy = signal(false);
  readonly result = signal<AnalyzeResponse | null>(null);
  readonly error = signal<ApiError | null>(null);
  /** What is in the input box right now, which may differ from what was analyzed. */
  readonly draft = signal('');

  /** True when the input was edited after the shown result was calculated. */
  readonly stale = computed(() => {
    const r = this.result();
    return r !== null && this.draft().trim() !== r.text;
  });

  submit(text: string): void {
    if (this.busy()) return;
    this.lastText = text;
    this.busy.set(true);
    this.error.set(null);
    // The previous result stays visible (dimmed) until this request finishes.
    this.api.analyze(text).subscribe({
      next: (r) => {
        this.result.set(r);
        this.busy.set(false);
      },
      error: (e: ApiError) => {
        // Drop the old result so it can't be mistaken for a result of the new text.
        this.result.set(null);
        this.error.set(e);
        this.busy.set(false);
      },
    });
  }

  /** Resend the last submitted text. */
  retry(): void {
    if (this.lastText !== null) this.submit(this.lastText);
  }
}
