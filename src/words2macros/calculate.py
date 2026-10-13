"""Nutrient math. Works at full precision; round only for the final result."""

from collections.abc import Callable, Iterable

from words2macros.models import Nutrients

FIELDS = ("calories_kcal", "protein_g", "carbs_g", "fat_g", "alcohol_g", "fiber_g")


def _apply(n: Nutrients, fn: Callable[[float], float]) -> Nutrients:
    """fn applied to every field; unknown (None) values stay unknown."""
    values = {f: getattr(n, f) for f in FIELDS}
    return Nutrients(**{f: None if v is None else fn(v) for f, v in values.items()})


def scale(per_100g: Nutrients, grams: float) -> Nutrients:
    """Nutrients for a given weight, from per-100 g values."""
    factor = grams / 100
    return _apply(per_100g, lambda v: v * factor)


def total(nutrients: Iterable[Nutrients]) -> Nutrients:
    """Sum several nutrient blocks into one.

    Unknown values are skipped, so a total is the sum of what is known. A field is
    unknown in the total only if it is unknown in every block.
    """
    nutrients = list(nutrients)
    if not nutrients:
        return Nutrients(**dict.fromkeys(FIELDS, 0))
    sums = {}
    for f in FIELDS:
        known = [getattr(n, f) for n in nutrients if getattr(n, f) is not None]
        sums[f] = sum(known) if known else None
    return Nutrients(**sums)


def rounded(nutrients: Nutrients, ndigits: int = 1) -> Nutrients:
    return _apply(nutrients, lambda v: round(v, ndigits))
