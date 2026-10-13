import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MAX_INPUT_CHARS } from '../meal.models';
import { EXAMPLE_MEALS, MealInputComponent } from './meal-input';

describe('MealInputComponent', () => {
  let fixture: ComponentFixture<MealInputComponent>;
  let el: HTMLElement;
  let emitted: string[];

  beforeEach(async () => {
    fixture = TestBed.createComponent(MealInputComponent);
    el = fixture.nativeElement;
    emitted = [];
    fixture.componentInstance.submitted.subscribe((t) => emitted.push(t));
    await fixture.whenStable();
  });

  const textarea = () => el.querySelector('textarea')!;
  const submitButton = () =>
    [...el.querySelectorAll('button')].find((b) => b.textContent?.includes('Calculate'))!;

  async function type(value: string) {
    textarea().value = value;
    textarea().dispatchEvent(new Event('input'));
    await fixture.whenStable();
  }

  it('submits the trimmed text', async () => {
    await type('  2 eggs  ');
    submitButton().click();
    expect(emitted).toEqual(['2 eggs']);
  });

  it('submits on Ctrl+Enter', async () => {
    await type('2 eggs');
    textarea().dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', ctrlKey: true }));
    expect(emitted).toEqual(['2 eggs']);
  });

  it('disables the button for empty or whitespace-only text', async () => {
    expect(submitButton().disabled).toBe(true);
    await type('   ');
    expect(submitButton().disabled).toBe(true);
  });

  it('disables the button and shows an error when the text is too long', async () => {
    await type('x'.repeat(MAX_INPUT_CHARS + 1));
    expect(submitButton().disabled).toBe(true);
    expect(el.querySelector('mat-error')?.textContent).toContain('Shorten the description');
  });

  it('disables the button and ignores Ctrl+Enter while busy', async () => {
    await type('2 eggs');
    fixture.componentRef.setInput('busy', true);
    await fixture.whenStable();
    expect(submitButton().disabled).toBe(true);
    textarea().dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', ctrlKey: true }));
    expect(emitted).toEqual([]);
  });

  it('starts with the initial text, ready to submit', async () => {
    const restored = TestBed.createComponent(MealInputComponent);
    restored.componentRef.setInput('initialText', '2 eggs');
    await restored.whenStable();
    const box: HTMLTextAreaElement = restored.nativeElement.querySelector('textarea');

    expect(box.value).toBe('2 eggs');
    expect(restored.nativeElement.textContent).toContain('6 / 2000');
    expect(restored.componentInstance.text.valid).toBe(true);
  });

  const clearButton = () =>
    [...el.querySelectorAll('button')].find((b) => b.textContent?.trim() === 'Clear')!;

  it('clears the box, reports the edit and puts the cursor back in it', async () => {
    const changes: string[] = [];
    fixture.componentInstance.textChange.subscribe((t) => changes.push(t));
    await type('2 eggs');

    clearButton().click();
    await fixture.whenStable();

    expect(textarea().value).toBe('');
    expect(changes.at(-1)).toBe(''); // so the saved draft is emptied too
    expect(document.activeElement).toBe(textarea());
    expect(clearButton().disabled).toBe(true);
  });

  it('disables Clear when the box is empty or while busy', async () => {
    expect(clearButton().disabled).toBe(true);
    await type('2 eggs');
    expect(clearButton().disabled).toBe(false);
    fixture.componentRef.setInput('busy', true);
    await fixture.whenStable();
    expect(clearButton().disabled).toBe(true);
  });

  it('fills the box from an example without submitting', async () => {
    const button = [...el.querySelectorAll('button')].find((b) =>
      b.textContent?.includes(EXAMPLE_MEALS[0].label),
    )!;
    button.click();
    await fixture.whenStable();
    expect(textarea().value).toBe(EXAMPLE_MEALS[0].text);
    expect(emitted).toEqual([]);
  });
});
