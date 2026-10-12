"""The full pipeline: parse -> match -> calculate -> validate."""

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
) -> MealResult:
    """Raises ParseError, MatchError or UsdaError with a user-safe message on failure."""
    client = client or make_client()
    parsed = parse_meal(text, client)
    # Each food waits on USDA and Bedrock for 1.5-2.5 s, so match them all at once
    # instead of one after another. At most MAX_ITEMS_PER_MEAL (15) threads; the
    # boto3 client is thread-safe. map() keeps the original order and re-raises the
    # first error.
    with ThreadPoolExecutor(max_workers=len(parsed.items)) as pool:
        matches = list(pool.map(lambda item: match_item(item, client, search), parsed.items))
    return build_meal_result(list(zip(parsed.items, matches, strict=True)))
