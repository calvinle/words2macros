import {
  Component,
  ElementRef,
  Injector,
  afterNextRender,
  effect,
  inject,
  viewChild,
} from '@angular/core';
import { MatToolbarModule } from '@angular/material/toolbar';

import { ErrorPanelComponent } from './meal/error-panel/error-panel';
import { LoadingStatusComponent } from './meal/loading-status/loading-status';
import { MealInputComponent } from './meal/meal-input/meal-input';
import { MealPageStore } from './meal/meal-page.store';
import { MealResultComponent } from './meal/meal-result/meal-result';

@Component({
  selector: 'app-root',
  imports: [
    ErrorPanelComponent,
    LoadingStatusComponent,
    MatToolbarModule,
    MealInputComponent,
    MealResultComponent,
  ],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  protected readonly store = inject(MealPageStore);
  private readonly injector = inject(Injector);
  private readonly mealInput = viewChild.required(MealInputComponent);
  private readonly results = viewChild<ElementRef<HTMLElement>>('results');

  constructor() {
    // On a phone the results start below the screen; bring a new result into view.
    // Not one restored after a refresh: the user is already where they left off.
    effect(() => {
      const result = this.store.result();
      if (result && result !== this.store.restoredResult) {
        afterNextRender(() => this.scrollToResults(), { injector: this.injector });
      }
    });
  }

  protected editDescription(): void {
    this.mealInput().focus();
  }

  private scrollToResults(): void {
    const el = this.results()?.nativeElement;
    if (!el || el.getBoundingClientRect().top < window.innerHeight - 80) return;
    const reduceMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
    el.scrollIntoView?.({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'start' });
  }
}
