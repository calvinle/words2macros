import { DatePipe, DecimalPipe } from '@angular/common';
import { Component, computed, input } from '@angular/core';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatIconModule } from '@angular/material/icon';

import { ITEM_CHECKS, WARNING_SEVERITY, energyFromMacros } from '../meal-format';
import { AnalyzeResponse } from '../meal.models';

/**
 * The four pipeline steps for one meal, using the response's own data.
 * Check verdicts come from the backend's warnings; nothing is re-calculated here.
 */
@Component({
  selector: 'app-calculation-details',
  imports: [DatePipe, DecimalPipe, MatExpansionModule, MatIconModule],
  templateUrl: './calculation-details.html',
  styleUrl: './calculation-details.scss',
})
export class CalculationDetailsComponent {
  readonly result = input.required<AnalyzeResponse>();

  readonly energyFromMacros = energyFromMacros;

  /** For each food, every check with its outcome. */
  readonly checks = computed(() =>
    this.result().items.map((_, i) =>
      ITEM_CHECKS.map((check) => {
        const flagged = this.result().warnings.some(
          (w) => w.item_index === i && w.code === check.code,
        );
        return {
          code: check.code,
          label: flagged ? check.flagged : check.passed,
          icon: !flagged ? 'check_circle' : WARNING_SEVERITY[check.code],
          status: flagged ? WARNING_SEVERITY[check.code] : 'passed',
        };
      }),
    ),
  );
}
