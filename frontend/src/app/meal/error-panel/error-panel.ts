import { Component, computed, input, output } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

import { ApiError } from '../meal-api.service';

/** What the user can do about an error: fix the text, or try again. */
export type ErrorKind = 'input' | 'retry' | 'unexpected';

const INPUT_CODES = ['INVALID_TEXT', 'NO_FOOD_FOUND', 'UNPARSEABLE', 'TOO_MANY_FOODS'];
const RETRY_CODES = [
  'MATCH_FAILED',
  'AI_UNAVAILABLE',
  'NUTRITION_DB_UNAVAILABLE',
  'THROTTLED',
  'NETWORK',
];

export function errorKind(code: string): ErrorKind {
  if (INPUT_CODES.includes(code)) return 'input';
  if (RETRY_CODES.includes(code)) return 'retry';
  return 'unexpected';
}

export function errorTitle(code: string): string {
  if (code === 'TOO_MANY_FOODS') return 'Too many foods';
  if (code === 'NETWORK') return "Can't reach the server";
  return {
    input: 'Check the description',
    retry: 'Try again in a moment',
    unexpected: 'Something went wrong',
  }[errorKind(code)];
}

/** An error with a title, the backend's message and the next step. */
@Component({
  selector: 'app-error-panel',
  imports: [MatButtonModule, MatIconModule],
  templateUrl: './error-panel.html',
  styleUrl: './error-panel.scss',
  host: { role: 'alert' },
})
export class ErrorPanelComponent {
  readonly error = input.required<ApiError>();
  readonly retry = output<void>();
  readonly edit = output<void>();

  readonly kind = computed(() => errorKind(this.error().code));
  readonly title = computed(() => errorTitle(this.error().code));
}
