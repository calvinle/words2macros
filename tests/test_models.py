import pytest
from pydantic import ValidationError

from words2macros.models import (
    FoodMatch,
    MealResult,
    MealWarning,
    Nutrients,
    ParsedItem,
    ParseResult,
)

POTATO = {
    "name": "russet potato",
    "preparation": "mashed",
    "grams": 190,
    "amount_source": "estimated",
    "assumption": "1 medium russet",
}

PER_100G = {"calories_kcal": 113, "protein_g": 1.9, "carbs_g": 17, "fat_g": 4.2}


def test_valid_parse_result():
    result = ParseResult.model_validate({"items": [POTATO]})

    assert result.items[0].grams == 190
    assert result.items[0].amount_source == "estimated"


def test_stated_amount_needs_no_assumption():
    item = ParsedItem.model_validate({"name": "gravy", "grams": 60, "amount_source": "stated"})

    assert item.assumption is None


@pytest.mark.parametrize(
    "changes",
    [
        {"name": ""},
        {"name": "   "},
        {"grams": -5},
        {"grams": 0},
        {"amount_source": "guessed"},
        {"assumption": None},
        {"calories": 200},
    ],
    ids=[
        "empty-name",
        "blank-name",
        "negative-grams",
        "zero-grams",
        "bad-amount-source",
        "estimated-without-assumption",
        "unknown-field",
    ],
)
def test_invalid_parsed_item(changes):
    with pytest.raises(ValidationError):
        ParsedItem.model_validate({**POTATO, **changes})


def test_missing_name_rejected():
    payload = {k: v for k, v in POTATO.items() if k != "name"}

    with pytest.raises(ValidationError):
        ParsedItem.model_validate(payload)


def test_empty_item_list_rejected():
    with pytest.raises(ValidationError):
        ParseResult.model_validate({"items": []})


def test_usda_match_needs_fdc_id():
    with pytest.raises(ValidationError):
        FoodMatch.model_validate(
            {"source": "usda", "description": "Potatoes, mashed", "per_100g": PER_100G}
        )


def test_ai_estimate_match_allows_no_fdc_id():
    match = FoodMatch.model_validate(
        {"source": "ai_estimate", "description": "house gravy", "per_100g": PER_100G}
    )

    assert match.fdc_id is None


def test_negative_nutrient_rejected():
    with pytest.raises(ValidationError):
        FoodMatch.model_validate(
            {
                "source": "usda",
                "fdc_id": 1,
                "description": "Potatoes, mashed",
                "per_100g": {**PER_100G, "fat_g": -1},
            }
        )


def test_fiber_is_optional():
    match = FoodMatch.model_validate(
        {"source": "ai_estimate", "description": "house gravy", "per_100g": PER_100G}
    )

    assert match.per_100g.fiber_g is None


@pytest.mark.parametrize("fiber", [-1, 17.1], ids=["negative", "more-than-carbs"])
def test_invalid_fiber_rejected(fiber):
    with pytest.raises(ValidationError):
        Nutrients.model_validate({**PER_100G, "fiber_g": fiber})


def test_fiber_equal_to_carbs_allowed():
    assert Nutrients.model_validate({**PER_100G, "fiber_g": 17}).fiber_g == 17


def test_valid_meal_result():
    meal = MealResult.model_validate(
        {
            "items": [
                {
                    **POTATO,
                    "match": {
                        "source": "usda",
                        "fdc_id": 2345,
                        "description": "Potatoes, mashed",
                        "per_100g": PER_100G,
                    },
                    "nutrients": {
                        "calories_kcal": 214.7,
                        "protein_g": 3.6,
                        "carbs_g": 32.3,
                        "fat_g": 8.0,
                    },
                }
            ],
            "totals": {"calories_kcal": 214.7, "protein_g": 3.6, "carbs_g": 32.3, "fat_g": 8.0},
            "warnings": [
                {"code": "AMOUNT_ESTIMATED", "message": "Assumed 1 medium russet.", "item_index": 0}
            ],
        }
    )

    assert meal.items[0].amount_source == "estimated"
    assert meal.warnings[0].code == "AMOUNT_ESTIMATED"


def test_unknown_warning_code_rejected():
    with pytest.raises(ValidationError):
        MealWarning.model_validate({"code": "SOMETHING_ELSE", "message": "x"})
