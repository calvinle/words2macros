import { TestBed } from '@angular/core/testing';

import { ThemeService } from './theme.service';

describe('ThemeService', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.style.colorScheme = '';
  });

  function create(): ThemeService {
    const service = TestBed.inject(ThemeService);
    TestBed.tick(); // run the effect that applies the theme
    return service;
  }

  it('starts from a saved choice', () => {
    localStorage.setItem('w2m.theme', 'dark');
    create();
    expect(document.documentElement.style.colorScheme).toBe('dark');
  });

  it('toggles the page color scheme and saves the choice', () => {
    localStorage.setItem('w2m.theme', 'light');
    const service = create();

    service.toggle();
    TestBed.tick();

    expect(service.theme()).toBe('dark');
    expect(document.documentElement.style.colorScheme).toBe('dark');
    expect(localStorage.getItem('w2m.theme')).toBe('dark');
  });
});
