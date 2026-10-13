import { Component, input } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';

import { Severity } from '../meal-format';

/** One warning or note: an icon plus the projected text. */
@Component({
  selector: 'app-warning-line',
  imports: [MatIconModule],
  template: `
    <mat-icon aria-hidden="true">{{ severity() === 'warning' ? 'warning' : 'info' }}</mat-icon>
    <span>
      @if (severity() === 'warning') {
        <span class="visually-hidden">Warning: </span>
      }
      <ng-content />
    </span>
  `,
  styles: `
    :host {
      display: flex;
      gap: 8px;
      align-items: flex-start;
      padding: 8px 12px;
      border-radius: 8px;
      font: var(--mat-sys-body-medium);
      background: var(--mat-sys-surface-container);
      color: var(--mat-sys-on-surface-variant);
    }
    :host(.warning) {
      background: light-dark(#fff4e5, #3d2a10);
      color: light-dark(#663c00, #ffdcb0);
      mat-icon {
        color: light-dark(#b45309, #fbbf24);
      }
    }
    mat-icon {
      flex: none;
      font-size: 20px;
      width: 20px;
      height: 20px;
    }
  `,
  host: { '[class.warning]': "severity() === 'warning'" },
})
export class WarningLineComponent {
  readonly severity = input<Severity>('info');
}
