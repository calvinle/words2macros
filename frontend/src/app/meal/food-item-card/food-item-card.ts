import { DecimalPipe } from '@angular/common';
import { Component, computed, input } from '@angular/core';
import { MatCardModule } from '@angular/material/card';

import { WARNING_SEVERITY } from '../meal-format';
import { ItemResult, MealWarning } from '../meal.models';
import { WarningLineComponent } from '../warning-line/warning-line';

/** One food: amount, macros, its warnings and the database record used. */
@Component({
  selector: 'app-food-item-card',
  imports: [DecimalPipe, MatCardModule, WarningLineComponent],
  templateUrl: './food-item-card.html',
  styleUrl: './food-item-card.scss',
})
export class FoodItemCardComponent {
  readonly item = input.required<ItemResult>();
  readonly warnings = input<MealWarning[]>([]);

  readonly severity = WARNING_SEVERITY;
  readonly estimated = computed(() => this.item().amount_source === 'estimated');
}
