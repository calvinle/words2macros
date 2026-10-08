"""Run sample meal descriptions through the real Bedrock parse step.

Usage: uv run --env-file .env python scripts/try_parse.py ["your own sentence" ...]
Each sentence is one Bedrock call (a fraction of a cent).
"""

import sys

from words2macros.parse import ParseError, parse_meal

SAMPLES = [
    "I had mashed potatoes from a medium russet potato with a serving of gravy.",
    "200 g grilled chicken breast, 1 cup of white rice and a tablespoon of olive oil.",
    "2 scrambled eggs, a slice of toast with butter, and black coffee.",
    "A handful of almonds and an apple.",
    "Big bowl of spaghetti with meat sauce and some parmesan on top.",
    "hello there",
]


def main() -> None:
    for text in sys.argv[1:] or SAMPLES:
        print(f"\n> {text}")
        try:
            result = parse_meal(text)
        except ParseError as e:
            print(f"  ERROR: {e}")
            continue
        for item in result.items:
            prep = f" ({item.preparation})" if item.preparation else ""
            print(f"  {item.name}{prep}: {item.grams:g} g [{item.amount_source}] {item.assumption}")


if __name__ == "__main__":
    main()
