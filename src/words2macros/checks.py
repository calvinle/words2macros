"""Sanity checks that produce user-facing warnings. None of them block a result."""

from words2macros.models import FoodMatch, MealWarning, ParsedItem

MAX_ITEM_GRAMS = 2000

# Energy check: warn only when the gap is large both relatively and absolutely,
# so low-calorie foods (lettuce) don't trigger it over a few kcal.
ENERGY_GAP_RATIO = 0.20
ENERGY_GAP_KCAL_PER_100G = 20


def label(item: ParsedItem) -> str:
    """Human-readable item name, e.g. "mashed russet potato"."""
    return f"{item.preparation} {item.name}" if item.preparation else item.name


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
                f"No amount was given for {label(item)}, so we assumed {item.assumption} "
                f"({format_grams(item.grams)} g). For more accurate results, enter a measured "
                "amount (grams, cups, etc.) and double check your input."
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
                f"We couldn't find {label(item)} in the USDA database, so its nutrients are an "
                "AI estimate. Treat these numbers as rough."
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
    name = label(item)
    return [
        MealWarning(
            code="OVER_2000G",
            message=(
                f"{name[0].upper()}{name[1:]} is listed as {format_grams(item.grams)} g, "
                "which is unusually large. Double check the amount."
            ),
            item_index=index,
        )
    ]


def check_item(item: ParsedItem, match: FoodMatch, index: int) -> list[MealWarning]:
    """All warnings for one item, in a stable order."""
    return [
        *check_amount_estimated(item, index),
        *check_nutrients_estimated(item, match, index),
        *check_energy(match, index),
        *check_weight(item, index),
    ]
