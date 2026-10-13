"""Step 2 of the pipeline: find the food record whose nutrients will be used.

USDA search returns the top records. The AI only picks one of them by ID; the
nutrient numbers always come from the USDA record. Only when nothing fits does
the AI estimate nutrients, and that match is labeled "ai_estimate".
"""

import json
from collections.abc import Callable
from typing import Any

from words2macros.bedrock import ask_validated
from words2macros.checks import label
from words2macros.errors import UserFacingError
from words2macros.models import FoodMatch, ParsedItem
from words2macros.usda import search_foods

CHOOSE_PROMPT = """\
You pick the USDA food record that best matches a food someone ate.

Rules:
- Match the food and its preparation: mashed is not baked, raw is not cooked. "dry" and "raw" \
mean an uncooked record ("Oats, dry", "Pasta, dry"), never a cooked one.
- The record must be the food itself, not a dish that contains it. For "gravy", pick a gravy, \
not "Biscuit with gravy".
- If the food is generic ("gravy", "cheese"), prefer a generic record ("Gravy, NFS") over a \
specific variety. NFS means "not further specified".
- Prefer plain records over flavored, sweetened, salted or fried ones unless the food says so.
- Return the fdc_id of the best record. Return null if none is a reasonable match.
"""

CHOOSE_SCHEMA = {
    "type": "object",
    "properties": {"fdc_id": {"type": ["integer", "null"]}},
    "required": ["fdc_id"],
    "additionalProperties": False,
}

ESTIMATE_PROMPT = """\
No database record was found for a food someone ate. Estimate typical nutrient values per \
100 g of the food as eaten, in its stated preparation.

- description: a short name for what you estimated, such as "Gravy, homemade".
- Values are per 100 g: calories in kcal, protein, carbs, fat, alcohol and fiber in grams.
- alcohol_g is 0 unless the food is an alcoholic drink or contains alcohol.
- fiber_g is total dietary fiber in grams. It is part of carbs_g, so it is never more than \
carbs_g.
"""

ESTIMATE_SCHEMA = {
    "type": "object",
    "properties": {
        "description": {"type": "string"},
        "calories_kcal": {"type": "number"},
        "protein_g": {"type": "number"},
        "carbs_g": {"type": "number"},
        "fat_g": {"type": "number"},
        "alcohol_g": {"type": "number"},
        "fiber_g": {"type": "number"},
    },
    "required": [
        "description",
        "calories_kcal",
        "protein_g",
        "carbs_g",
        "fat_g",
        "alcohol_g",
        "fiber_g",
    ],
    "additionalProperties": False,
}

NO_MATCH = object()  # the AI validly answered "none of these fit"


class MatchError(UserFacingError):
    """No usable food record or estimate."""

    def __init__(self, message: str):
        super().__init__("MATCH_FAILED", message)


def match_item(
    item: ParsedItem,
    client: Any,
    search: Callable[[str], list[FoodMatch]] = search_foods,
) -> FoodMatch:
    candidates = search(label(item))
    if not candidates and item.preparation:
        candidates = search(item.name)

    if candidates:
        chosen = choose_match(item, candidates, client)
        if chosen is not None:
            return chosen
    return estimate_nutrients(item, client)


def choose_match(item: ParsedItem, candidates: list[FoodMatch], client: Any) -> FoodMatch | None:
    """The candidate the AI picked, or None if it said none fit."""
    by_id = {c.fdc_id: c for c in candidates}

    def validate(data: Any) -> Any:
        if not isinstance(data, dict) or "fdc_id" not in data:
            raise ValueError("expected an object with fdc_id")
        fdc_id = data["fdc_id"]
        if fdc_id is None:
            return NO_MATCH
        if fdc_id not in by_id:
            raise ValueError(f"fdc_id {fdc_id!r} was not one of the candidates")
        return by_id[fdc_id]

    text = json.dumps(
        {
            "food": {"name": item.name, "preparation": item.preparation},
            "records": [
                {
                    "fdc_id": c.fdc_id,
                    "description": c.description,
                    "kcal_per_100g": c.per_100g.calories_kcal,
                }
                for c in candidates
            ],
        }
    )
    result = ask_validated(
        client,
        system=CHOOSE_PROMPT,
        text=text,
        schema=CHOOSE_SCHEMA,
        schema_name="food_match",
        validate=validate,
    )
    if result is None:
        raise MatchError(f"A database match for {label(item)} couldn't be chosen. Try again.")
    return None if result is NO_MATCH else result


def estimate_nutrients(item: ParsedItem, client: Any) -> FoodMatch:
    def validate(data: Any) -> FoodMatch:
        if not isinstance(data, dict):
            raise ValueError("expected an object")
        return FoodMatch(
            source="ai_estimate",
            description=data.get("description", ""),
            per_100g={k: data.get(k) for k in ESTIMATE_SCHEMA["required"][1:]},
        )

    result = ask_validated(
        client,
        system=ESTIMATE_PROMPT,
        text=json.dumps({"name": item.name, "preparation": item.preparation}),
        schema=ESTIMATE_SCHEMA,
        schema_name="nutrient_estimate",
        validate=validate,
    )
    if result is None:
        raise MatchError(f"Nutrients for {label(item)} couldn't be found or estimated.")
    return result
