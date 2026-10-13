"""Run meal descriptions through the full pipeline (real Bedrock and USDA).

Usage: uv run --env-file .env python scripts/try_meal.py ["your own sentence" ...]
Each food costs one USDA search and one Bedrock call, plus one Bedrock call per sentence.
"""

import sys

from words2macros.match import MatchError
from words2macros.parse import ParseError
from words2macros.pipeline import analyze_meal
from words2macros.usda import UsdaError

SAMPLES = [
    "I had mashed potatoes from a medium russet potato with a serving of gravy.",
    "200 g grilled chicken breast, 1 cup of white rice and a tablespoon of olive oil.",
    "2 scrambled eggs, a slice of toast with butter, and black coffee.",
    "A handful of almonds and an apple.",
]


def macros(n) -> str:
    fiber = "n/a" if n.fiber_g is None else f"{n.fiber_g:g} g"
    return (
        f"{n.calories_kcal:g} kcal | P {n.protein_g:g} g | C {n.carbs_g:g} g "
        f"(fiber {fiber}) | F {n.fat_g:g} g"
    )


def main() -> None:
    for text in sys.argv[1:] or SAMPLES:
        print(f"\n> {text}")
        try:
            meal = analyze_meal(text)
        except (ParseError, MatchError, UsdaError) as e:
            print(f"  ERROR: {e}")
            continue
        for item in meal.items:
            source = f"USDA {item.match.fdc_id}" if item.match.fdc_id else "AI estimate"
            print(f"  {item.name}, {item.grams:g} g [{item.amount_source}]")
            print(f"      match: {item.match.description} ({source})")
            print(f"      {macros(item.nutrients)}")
        print(f"  TOTAL: {macros(meal.totals)}")
        for w in meal.warnings:
            print(f"  ! {w.code}: {w.message}")


if __name__ == "__main__":
    main()
