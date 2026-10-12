import { TestBed } from '@angular/core/testing';

import { ApiError } from '../meal-api.service';
import { ErrorPanelComponent, errorKind, errorTitle } from './error-panel';

async function render(error: ApiError) {
  const fixture = TestBed.createComponent(ErrorPanelComponent);
  fixture.componentRef.setInput('error', error);
  const events: string[] = [];
  fixture.componentInstance.retry.subscribe(() => events.push('retry'));
  fixture.componentInstance.edit.subscribe(() => events.push('edit'));
  await fixture.whenStable();
  const el: HTMLElement = fixture.nativeElement;
  return { el, events, button: el.querySelector('button')! };
}

describe('error grouping', () => {
  it.each([
    ['TOO_MANY_FOODS', 'input', 'Too many foods'],
    ['NO_FOOD_FOUND', 'input', 'Check the description'],
    ['UNPARSEABLE', 'input', 'Check the description'],
    ['AI_UNAVAILABLE', 'retry', 'Try again in a moment'],
    ['THROTTLED', 'retry', 'Try again in a moment'],
    ['NETWORK', 'retry', "Can't reach the server"],
    ['INTERNAL_ERROR', 'unexpected', 'Something went wrong'],
    ['SOMETHING_NEW', 'unexpected', 'Something went wrong'],
  ])('%s is %s, titled "%s"', (code, kind, title) => {
    expect(errorKind(code)).toBe(kind);
    expect(errorTitle(code)).toBe(title);
  });
});

describe('ErrorPanelComponent', () => {
  it('offers to edit the description for input problems', async () => {
    const { el, events, button } = await render(new ApiError('NO_FOOD_FOUND', 'No food found.'));
    expect(el.querySelector('h2')?.textContent).toBe('Check the description');
    expect(el.textContent).toContain('No food found.');
    expect(button.textContent).toContain('Edit description');
    button.click();
    expect(events).toEqual(['edit']);
  });

  it('offers to try again for temporary problems', async () => {
    const { events, button } = await render(new ApiError('THROTTLED', 'Busy.'));
    expect(button.textContent).toContain('Try again');
    button.click();
    expect(events).toEqual(['retry']);
  });

  it('shows the reference only when there is one', async () => {
    const withId = await render(new ApiError('INTERNAL_ERROR', 'Oops.', 'req-9'));
    expect(withId.el.querySelector('.reference')?.textContent).toContain('req-9');
    const without = await render(new ApiError('NETWORK', 'Offline.'));
    expect(without.el.querySelector('.reference')).toBeNull();
  });
});
