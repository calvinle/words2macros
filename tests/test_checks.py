from words2macros.checks import (
    check_amount_estimated,
    check_calorie_dense_estimate,
    check_energy,
    check_nutrients_estimated,
    check_weight,
    format_grams,
)
from words2macros.models import FoodMatch, ParsedItem


def item(**overrides) -> ParsedItem:
    fields = {
        "name": "russet potato",
        "preparation": "mashed",
        "grams": 190,
        "amount_source": "estimated",
        "assumption": "1 medium russet",
    }
    return ParsedItem(**{**fields, **overrides})


def match(source="usda", **per_100g) -> FoodMatch:
    nutrients = {"calories_kcal": 113, "protein_g": 1.9, "carbs_g": 17, "fat_g": 4.2}
    return FoodMatch(
        source=source,
        fdc_id=1 if source == "usda" else None,
        description="Potatoes, mashed",
        per_100g={**nutrients, **per_100g},
    )


def test_format_grams():
    assert format_grams(190.0) == "190"
    assert format_grams(2500) == "2,500"
    assert format_grams(12.5) == "12.5"


def test_estimated_amount_warns_with_assumption():
    [warning] = check_amount_estimated(item(), 0)

    assert warning.code == "AMOUNT_ESTIMATED"
    assert warning.item_index == 0
    assert warning.message == (
        "An estimated 190 g of mashed russet potato was used (assumed: 1 medium russet). "
        "For more accurate results, enter a measured amount (grams, cups, etc.) and double "
        "check your input."
    )


def test_estimated_calorie_dense_food_warns():
    cheddar = item(name="cheddar cheese", preparation=None, grams=28, assumption="1 slice")

    [warning] = check_calorie_dense_estimate(cheddar, match(calories_kcal=404), 0)

    assert warning.code == "CALORIE_DENSE_ESTIMATE"
    assert warning.message == (
        "Cheddar cheese is calorie dense (404 kcal per 100 g), so the estimated portion has a "
        "big effect on the total. Weigh or measure it for an accurate result."
    )


def test_estimated_low_density_food_does_not_warn():
    assert check_calorie_dense_estimate(item(), match(), 0) == []


def test_stated_calorie_dense_food_does_not_warn():
    stated = item(amount_source="stated", assumption=None)

    assert check_calorie_dense_estimate(stated, match(calories_kcal=404), 0) == []


def test_stated_amount_does_not_warn():
    assert check_amount_estimated(item(amount_source="stated"), 0) == []


def test_ai_estimated_nutrients_warn():
    [warning] = check_nutrients_estimated(
        item(name="house gravy", preparation=None), match("ai_estimate"), 2
    )

    assert warning.code == "NUTRIENTS_ESTIMATED"
    assert warning.item_index == 2
    assert warning.message.startswith("House gravy was not found")


def test_usda_nutrients_do_not_warn():
    assert check_nutrients_estimated(item(), match(), 0) == []


def test_energy_mismatch_warns():
    # 4*2 + 4*10 + 9*1 = 57 kcal from macros vs 300 listed.
    [warning] = check_energy(match(calories_kcal=300, protein_g=2, carbs_g=10, fat_g=1), 0)

    assert warning.code == "ENERGY_MISMATCH"
    assert "'Potatoes, mashed'" in warning.message


def test_consistent_energy_does_not_warn():
    assert check_energy(match(), 0) == []


def test_small_absolute_gap_does_not_warn():
    # Lettuce: 19 kcal from macros vs 15 listed is a 21% gap but only 4 kcal.
    assert check_energy(match(calories_kcal=15, protein_g=1.4, carbs_g=2.9, fat_g=0.2), 0) == []


def test_small_relative_gap_does_not_warn():
    # 4*20 + 4*50 + 9*30 = 550 kcal from macros vs 520 listed is 30 kcal but only 5%.
    assert check_energy(match(calories_kcal=520, protein_g=20, carbs_g=50, fat_g=30), 0) == []


def test_over_2000g_warns():
    [warning] = check_weight(item(grams=2500), 1)

    assert warning.code == "OVER_2000G"
    assert warning.message == (
        "Mashed russet potato is listed as 2,500 g, which is unusually large. "
        "Double check the amount."
    )


def test_2000g_exactly_does_not_warn():
    assert check_weight(item(grams=2000), 0) == []
