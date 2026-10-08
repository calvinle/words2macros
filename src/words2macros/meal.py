"""Combine parsed items and their food matches into a validated meal result."""

from words2macros.calculate import rounded, scale, total
from words2macros.checks import check_item
from words2macros.models import FoodMatch, ItemResult, MealResult, ParsedItem


def build_meal_result(pairs: list[tuple[ParsedItem, FoodMatch]]) -> MealResult:
    """Calculate per-item and per-meal nutrients and attach warnings.

    Totals are summed from unrounded item values, so they can differ from the sum
    of the displayed (rounded) item values by a tenth or so.
    """
    exact = [scale(match.per_100g, item.grams) for item, match in pairs]

    items = [
        ItemResult(**item.model_dump(), match=match, nutrients=rounded(nutrients))
        for (item, match), nutrients in zip(pairs, exact, strict=True)
    ]
    warnings = [
        warning
        for index, (item, match) in enumerate(pairs)
        for warning in check_item(item, match, index)
    ]

    return MealResult(items=items, totals=rounded(total(exact)), warnings=warnings)
