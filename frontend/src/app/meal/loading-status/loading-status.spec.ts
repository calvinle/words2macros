import { TestBed } from '@angular/core/testing';

import { LOADING_MESSAGES, LoadingStatusComponent } from './loading-status';

describe('LoadingStatusComponent', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  function render() {
    const fixture = TestBed.createComponent(LoadingStatusComponent);
    fixture.detectChanges();
    const text = () => {
      fixture.detectChanges();
      return (fixture.nativeElement as HTMLElement).querySelector('p')?.textContent;
    };
    return { fixture, text };
  }

  it('changes its message as time passes', () => {
    const { text } = render();
    expect(text()).toBe(LOADING_MESSAGES[0].text);
    vi.advanceTimersByTime(3000);
    expect(text()).toBe(LOADING_MESSAGES[1].text);
    vi.advanceTimersByTime(12000);
    expect(text()).toBe(LOADING_MESSAGES[2].text);
  });

  it('stops its timers when removed', () => {
    const { fixture } = render();
    fixture.destroy();
    expect(vi.getTimerCount()).toBe(0);
  });
});
