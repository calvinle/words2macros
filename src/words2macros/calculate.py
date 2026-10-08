"""Nutrient math. Works at full precision; round only for the final result."""

from collections.abc import Iterable

from words2macros.models import Nutrients

FIELDS = ("calories_kcal", "protein_g", "carbs_g", "fat_g")


def scale(per_100g: Nutrients, grams: float) -> Nutrients:
    """Nutrients for a given weight, from per-100 g values."""
    factor = grams / 100
    return Nutrients(**{f: getattr(per_100g, f) * factor for f in FIELDS})


def total(nutrients: Iterable[Nutrients]) -> Nutrients:
    """Sum several nutrient blocks into one."""
    nutrients = list(nutrients)
    return Nutrients(**{f: sum(getattr(n, f) for n in nutrients) for f in FIELDS})


def rounded(nutrients: Nutrients, ndigits: int = 1) -> Nutrients:
    return Nutrients(**{f: round(getattr(nutrients, f), ndigits) for f in FIELDS})
