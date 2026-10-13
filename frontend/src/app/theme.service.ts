import { DOCUMENT, Injectable, inject, signal } from '@angular/core';

export type Theme = 'light' | 'dark';

const STORAGE_KEY = 'w2m.theme';

/**
 * Light or dark mode. Starts from the user's saved choice, else the system setting.
 * Angular Material's colors use CSS light-dark(), so setting `color-scheme` on <html>
 * is all it takes to switch every component.
 */
@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly document = inject(DOCUMENT);
  readonly theme = signal<Theme>(this.savedTheme() ?? this.systemTheme());

  constructor() {
    this.apply(this.theme());
  }

  toggle(): void {
    const next: Theme = this.theme() === 'dark' ? 'light' : 'dark';
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // Storage blocked (private mode): the choice lasts until the page closes.
    }

    // Crossfade the whole page where the browser supports View Transitions; the
    // browser snapshots the old look, runs the callback, then fades to the new one.
    const reduceMotion = this.document.defaultView?.matchMedia?.(
      '(prefers-reduced-motion: reduce)',
    ).matches;
    if (!this.document.startViewTransition || reduceMotion) {
      this.apply(next);
      return;
    }
    this.document.startViewTransition(() => this.apply(next));
  }

  private apply(theme: Theme): void {
    this.theme.set(theme);
    this.document.documentElement.style.colorScheme = theme;
  }

  private savedTheme(): Theme | null {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved === 'light' || saved === 'dark' ? saved : null;
    } catch {
      return null;
    }
  }

  private systemTheme(): Theme {
    return this.document.defaultView?.matchMedia?.('(prefers-color-scheme: dark)').matches
      ? 'dark'
      : 'light';
  }
}
