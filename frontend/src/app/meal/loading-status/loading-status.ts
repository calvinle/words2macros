import { Component, DestroyRef, inject, signal } from '@angular/core';
import { MatProgressBarModule } from '@angular/material/progress-bar';

/**
 * Timed messages while a request runs. The API answers once at the end, so these
 * describe what is likely happening, without claiming any step has finished.
 * Timings come from the Lambda logs: parsing takes about 3 s, then about 2 s per food.
 */
export const LOADING_MESSAGES = [
  { afterMs: 0, text: 'Reading the meal description...' },
  { afterMs: 3000, text: 'Looking up each food in the USDA database...' },
  { afterMs: 15000, text: 'This is taking longer than usual. Larger meals take more time.' },
];

@Component({
  selector: 'app-loading-status',
  imports: [MatProgressBarModule],
  template: `
    <mat-progress-bar mode="indeterminate" aria-hidden="true" />
    <p>{{ message() }}</p>
  `,
  styles: `
    :host {
      display: block;
    }
    p {
      margin: 8px 0 0;
      font: var(--mat-sys-body-medium);
      color: var(--mat-sys-on-surface-variant);
    }
  `,
  host: { role: 'status' },
})
export class LoadingStatusComponent {
  readonly message = signal(LOADING_MESSAGES[0].text);

  constructor() {
    // Shown only while busy, so each request gets a fresh component and fresh timers.
    const timers = LOADING_MESSAGES.slice(1).map((m) =>
      setTimeout(() => this.message.set(m.text), m.afterMs),
    );
    inject(DestroyRef).onDestroy(() => timers.forEach(clearTimeout));
  }
}
