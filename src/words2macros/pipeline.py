"""The full pipeline: parse -> match -> calculate -> validate."""

from collections.abc import Callable
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
    pairs = [(item, match_item(item, client, search)) for item in parsed.items]
    return build_meal_result(pairs)
