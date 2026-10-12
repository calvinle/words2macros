import { Component, computed, input } from '@angular/core';

import { CalculationDetailsComponent } from '../calculation-details/calculation-details';
import { FoodItemCardComponent } from '../food-item-card/food-item-card';
import {
  WARNING_SEVERITY,
  estimatedCount,
  mealLevelWarnings,
  warningsForItem,
} from '../meal-format';
import { AnalyzeResponse } from '../meal.models';
import { MealTotalsComponent } from '../meal-totals/meal-totals';
import { WarningLineComponent } from '../warning-line/warning-line';

/** Arranges one analyzed meal: totals, a summary of estimates, then each food. */
@Component({
  selector: 'app-meal-result',
  imports: [
    CalculationDetailsComponent,
    FoodItemCardComponent,
    MealTotalsComponent,
    WarningLineComponent,
  ],
  templateUrl: './meal-result.html',
  styleUrl: './meal-result.scss',
})
export class MealResultComponent {
  readonly result = input.required<AnalyzeResponse>();
  readonly stale = input(false); // the input was edited after this result

  readonly severity = WARNING_SEVERITY;
  readonly estimated = computed(() => estimatedCount(this.result().items));
  readonly mealWarnings = computed(() => mealLevelWarnings(this.result().warnings));
  readonly itemWarnings = computed(() =>
    this.result().items.map((_, i) => warningsForItem(this.result().warnings, i)),
  );
}
