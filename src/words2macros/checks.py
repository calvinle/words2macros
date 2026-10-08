"""Sanity checks that produce user-facing warnings. None of them block a result.

Messages use a neutral voice (no "we").
"""

from words2macros.models import FoodMatch, MealWarning, ParsedItem

MAX_ITEM_GRAMS = 2000

# Energy check: warn only when the gap is large both relatively and absolutely,
# so low-calorie foods (lettuce) don't trigger it over a few kcal.
ENERGY_GAP_RATIO = 0.20
ENERGY_GAP_KCAL_PER_100G = 20

# Estimated portions of foods at or above this density (cheese, nuts, bread, steak)
# swing the total much more than the same guess for a potato.
CALORIE_DENSE_KCAL_PER_100G = 250


def label(item: ParsedItem) -> str:
    """Human-readable item name, e.g. "mashed russet potato"."""
    return f"{item.preparation} {item.name}" if item.preparation else item.name


def capitalized(text: str) -> str:
    return text[:1].upper() + text[1:]


def format_grams(grams: float) -> str:
    """190.0 -> "190", 2500 -> "2,500", 12.5 -> "12.5"."""
    return f"{grams:,.1f}".rstrip("0").rstrip(".")


def check_amount_estimated(item: ParsedItem, index: int) -> list[MealWarning]:
    if item.amount_source != "estimated":
        return []
    return [
        MealWarning(
            code="AMOUNT_ESTIMATED",
            message=(
                f"An estimated {format_grams(item.grams)} g of {label(item)} was used "
                f"(assumed: {item.assumption}). For more accurate results, enter a measured "
                "amount (grams, cups, etc.) and double check your input."
            ),
            item_index=index,
        )
    ]


def check_calorie_dense_estimate(
    item: ParsedItem, match: FoodMatch, index: int
) -> list[MealWarning]:
    kcal = match.per_100g.calories_kcal
    if item.amount_source != "estimated" or kcal < CALORIE_DENSE_KCAL_PER_100G:
        return []
    return [
        MealWarning(
            code="CALORIE_DENSE_ESTIMATE",
            message=(
                f"{capitalized(label(item))} is calorie dense ({kcal:.0f} kcal per 100 g), so "
                "the estimated portion has a big effect on the total. Weigh or measure it for "
                "an accurate result."
            ),
            item_index=index,
        )
    ]


def check_nutrients_estimated(item: ParsedItem, match: FoodMatch, index: int) -> list[MealWarning]:
    if match.source != "ai_estimate":
        return []
    return [
        MealWarning(
            code="NUTRIENTS_ESTIMATED",
            message=(
                f"{capitalized(label(item))} was not found in the USDA database, so its "
                "nutrients are an AI estimate. Treat these numbers as rough."
            ),
            item_index=index,
        )
    ]


def check_energy(match: FoodMatch, index: int) -> list[MealWarning]:
    n = match.per_100g
    from_macros = 4 * n.protein_g + 4 * n.carbs_g + 9 * n.fat_g
    gap = abs(n.calories_kcal - from_macros)
    larger = max(n.calories_kcal, from_macros)
    if gap <= ENERGY_GAP_KCAL_PER_100G or gap <= ENERGY_GAP_RATIO * larger:
        return []
    return [
        MealWarning(
            code="ENERGY_MISMATCH",
            message=(
                f"The calories for '{match.description}' don't add up from its protein, carbs "
                "and fat, so this may be a poor database match. Check the matched food."
            ),
            item_index=index,
        )
    ]


def check_weight(item: ParsedItem, index: int) -> list[MealWarning]:
    if item.grams <= MAX_ITEM_GRAMS:
        return []
    return [
        MealWarning(
            code="OVER_2000G",
            message=(
                f"{capitalized(label(item))} is listed as {format_grams(item.grams)} g, "
                "which is unusually large. Double check the amount."
            ),
            item_index=index,
        )
    ]


def check_item(item: ParsedItem, match: FoodMatch, index: int) -> list[MealWarning]:
    """All warnings for one item, in a stable order."""
    return [
        *check_amount_estimated(item, index),
        *check_calorie_dense_estimate(item, match, index),
        *check_nutrients_estimated(item, match, index),
        *check_energy(match, index),
        *check_weight(item, index),
    ]
