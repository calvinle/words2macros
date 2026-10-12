"""The full pipeline: parse -> match -> calculate -> validate."""

import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from words2macros.bedrock import make_client
from words2macros.match import match_item
from words2macros.meal import build_meal_result
from words2macros.models import FoodMatch, MealResult
from words2macros.parse import parse_meal
from words2macros.usda import search_foods


def analyze_meal(
    text: str,
    client: Any = None,
    search: Callable[[str], list[FoodMatch]] = search_foods,
    timings: dict[str, int] | None = None,
) -> MealResult:
    """Raises ParseError, MatchError or UsdaError with a user-safe message on failure.

    Fills `timings` with parse_ms and match_ms as each step finishes, so a failed
    request still reports how long the steps before the failure took.
    """
    timings = {} if timings is None else timings
    client = client or make_client()

    started = time.monotonic()
    parsed = parse_meal(text, client)
    timings["parse_ms"] = elapsed_ms(started)

    # Each food waits on USDA and Bedrock for 1.5-2.5 s, so match them all at once
    # instead of one after another. At most MAX_ITEMS_PER_MEAL (15) threads; the
    # boto3 client is thread-safe. map() keeps the original order and re-raises the
    # first error.
    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=len(parsed.items)) as pool:
        matches = list(pool.map(lambda item: match_item(item, client, search), parsed.items))
    timings["match_ms"] = elapsed_ms(started)
    return build_meal_result(list(zip(parsed.items, matches, strict=True)))


def elapsed_ms(started: float) -> int:
    return round((time.monotonic() - started) * 1000)
