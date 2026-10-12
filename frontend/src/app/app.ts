import { Component, inject, signal } from '@angular/core';
import { MatToolbarModule } from '@angular/material/toolbar';

import { ApiError, MealApiService } from './meal/meal-api.service';
import { MealInputComponent } from './meal/meal-input/meal-input';
import { MealResultComponent } from './meal/meal-result/meal-result';
import { AnalyzeResponse } from './meal/meal.models';

@Component({
  selector: 'app-root',
  imports: [MatToolbarModule, MealInputComponent, MealResultComponent],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  private readonly api = inject(MealApiService);

  protected readonly busy = signal(false);
  protected readonly result = signal<AnalyzeResponse | null>(null);
  protected readonly error = signal<ApiError | null>(null);

  protected onSubmit(text: string): void {
    this.busy.set(true);
    this.error.set(null);
    this.api.analyze(text).subscribe({
      next: (r) => {
        this.result.set(r);
        this.busy.set(false);
      },
      error: (e: ApiError) => {
        this.error.set(e);
        this.busy.set(false);
      },
    });
  }
}
