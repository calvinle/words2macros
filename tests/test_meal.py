"""End to end for Steps 3-4, using the CLAUDE.md example sentence:
"I had mashed potatoes from a medium russet potato with a serving of gravy."
"""

from words2macros.meal import build_meal_result
from words2macros.models import FoodMatch, Nutrients, ParsedItem

POTATO = ParsedItem(
    name="russet potato",
    preparation="mashed",
    grams=190,
    amount_source="estimated",
    assumption="1 medium russet",
)
GRAVY = ParsedItem(name="gravy", grams=60, amount_source="stated")

POTATO_MATCH = FoodMatch(
    source="usda",
    fdc_id=1,
    description="Potatoes, mashed",
    per_100g=Nutrients(calories_kcal=113, protein_g=1.9, carbs_g=17, fat_g=4.2, fiber_g=1.2),
)
GRAVY_MATCH = FoodMatch(
    source="usda",
    fdc_id=2,
    description="Gravy, brown",
    per_100g=Nutrients(calories_kcal=50, protein_g=1.5, carbs_g=5, fat_g=2.5, fiber_g=0.4),
)


def test_meal_items_and_totals():
    meal = build_meal_result([(POTATO, POTATO_MATCH), (GRAVY, GRAVY_MATCH)])

    assert meal.items[0].nutrients == Nutrients(
        calories_kcal=214.7, protein_g=3.6, carbs_g=32.3, fat_g=8.0, fiber_g=2.3
    )
    assert meal.items[1].nutrients == Nutrients(
        calories_kcal=30.0, protein_g=0.9, carbs_g=3.0, fat_g=1.5, fiber_g=0.2
    )
    assert meal.totals == Nutrients(
        calories_kcal=244.7, protein_g=4.5, carbs_g=35.3, fat_g=9.5, fiber_g=2.5
    )


def test_amount_source_carried_through():
    meal = build_meal_result([(POTATO, POTATO_MATCH), (GRAVY, GRAVY_MATCH)])

    assert [i.amount_source for i in meal.items] == ["estimated", "stated"]
    assert meal.items[0].assumption == "1 medium russet"


def test_only_estimated_item_warns():
    meal = build_meal_result([(POTATO, POTATO_MATCH), (GRAVY, GRAVY_MATCH)])

    assert [(w.code, w.item_index) for w in meal.warnings] == [("AMOUNT_ESTIMATED", 0)]


def test_dry_amount_flag_carried_through_with_a_note():
    dry = GRAVY.model_copy(update={"dry_amount": True})

    meal = build_meal_result([(dry, GRAVY_MATCH)])

    assert meal.items[0].dry_amount is True
    assert [w.code for w in meal.warnings] == ["DRY_AMOUNT"]


def test_unreported_fiber_is_left_out_of_the_total_with_a_warning():
    no_fiber = GRAVY_MATCH.model_copy(
        update={"per_100g": GRAVY_MATCH.per_100g.model_copy(update={"fiber_g": None})}
    )

    meal = build_meal_result([(POTATO, POTATO_MATCH), (GRAVY, no_fiber)])

    assert meal.items[1].nutrients.fiber_g is None
    assert meal.totals.fiber_g == 2.3  # the potato only
    assert ("FIBER_NOT_REPORTED", 1) in [(w.code, w.item_index) for w in meal.warnings]
