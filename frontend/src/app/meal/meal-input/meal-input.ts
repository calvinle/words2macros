import { TextFieldModule } from '@angular/cdk/text-field';
import {
  Component,
  ElementRef,
  OnInit,
  computed,
  input,
  output,
  signal,
  viewChild,
} from '@angular/core';
import { outputFromObservable, takeUntilDestroyed, toSignal } from '@angular/core/rxjs-interop';
import { AbstractControl, FormControl, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { ErrorStateMatcher } from '@angular/material/core';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';

import { MAX_INPUT_CHARS, MAX_ITEMS_PER_MEAL } from '../meal.models';

export const EXAMPLE_MEALS = [
  {
    label: 'Mashed potato + gravy',
    text: 'I had mashed potatoes from a medium russet potato with a serving of gravy.',
  },
  {
    label: 'Chicken rice bowl',
    text: '150 g grilled chicken breast, 1 cup cooked white rice and half an avocado.',
  },
  {
    label: 'Oatmeal',
    text: 'Oatmeal made with 1/2 cup dry oats and 1 cup 2% milk, topped with a banana.',
  },
];

/** Show the field in red only when the text is too long, not while it is still empty. */
const tooLongMatcher: ErrorStateMatcher = {
  isErrorState: (control: AbstractControl | null) => !!control?.hasError('maxlength'),
};

/** The meal description box. Collects text only; the parent calls the API. */
@Component({
  selector: 'app-meal-input',
  imports: [
    ReactiveFormsModule,
    TextFieldModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
  ],
  templateUrl: './meal-input.html',
  styleUrl: './meal-input.scss',
})
export class MealInputComponent implements OnInit {
  readonly busy = input(false); // true while a request runs
  readonly initialText = input(''); // e.g. the description restored after a refresh
  readonly submitted = output<string>(); // the trimmed description

  readonly maxChars = MAX_INPUT_CHARS;
  readonly maxItems = MAX_ITEMS_PER_MEAL;
  readonly examples = EXAMPLE_MEALS;
  readonly tooLongMatcher = tooLongMatcher;

  readonly text = new FormControl('', {
    nonNullable: true,
    validators: [
      Validators.required,
      Validators.pattern(/\S/), // not whitespace only
      Validators.maxLength(MAX_INPUT_CHARS),
    ],
  });

  /** Every edit, so the page can tell when a shown result no longer matches the text. */
  readonly textChange = outputFromObservable(this.text.valueChanges);

  private readonly value = toSignal(this.text.valueChanges, { initialValue: '' });
  readonly length = computed(() => this.value().length);
  private readonly textarea = viewChild.required<ElementRef<HTMLTextAreaElement>>('textarea');

  /** The text removed by Clear, while Undo is offered; null otherwise. */
  readonly undoText = signal<string | null>(null);

  constructor() {
    // Any new text (typing, an example, Undo itself) withdraws the offer, so Undo
    // never overwrites what is in the box.
    this.text.valueChanges.pipe(takeUntilDestroyed()).subscribe(() => this.undoText.set(null));
  }

  ngOnInit(): void {
    if (this.initialText()) this.text.setValue(this.initialText());
  }

  submit(): void {
    if (this.busy() || this.text.invalid) return;
    this.submitted.emit(this.text.value.trim());
  }

  useExample(text: string): void {
    this.text.setValue(text);
  }

  /** Empties the box (and so the saved draft), puts the cursor back in it and offers Undo. */
  clear(): void {
    const previous = this.text.value;
    this.text.setValue('');
    this.undoText.set(previous); // after setValue, whose change event withdraws Undo
    this.focus();
  }

  undo(): void {
    const previous = this.undoText();
    if (previous === null) return;
    this.text.setValue(previous);
    this.focus();
  }

  focus(): void {
    this.textarea().nativeElement.focus();
  }
}
