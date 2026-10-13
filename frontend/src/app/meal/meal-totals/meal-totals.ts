import { DecimalPipe } from '@angular/common';
import { Component, computed, input } from '@angular/core';
import { MatCardModule } from '@angular/material/card';

import { macroShares } from '../meal-format';
import { Nutrients } from '../meal.models';

/** Meal totals and the calories-from-macros bar. */
@Component({
  selector: 'app-meal-totals',
  imports: [DecimalPipe, MatCardModule],
  templateUrl: './meal-totals.html',
  styleUrl: './meal-totals.scss',
})
export class MealTotalsComponent {
  readonly totals = input.required<Nutrients>();
  readonly estimated = input(false); // any amount in the meal was estimated
  readonly fiberIncomplete = input(false); // some food has no fiber value

  readonly shares = computed(() => macroShares(this.totals()));
  readonly barLabel = computed(() => {
    const s = this.shares();
    return s && `Calories from protein ${s.protein}%, carbs ${s.carbs}%, fat ${s.fat}%`;
  });
}
