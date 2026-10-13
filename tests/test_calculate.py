import pytest

from words2macros.calculate import rounded, scale, total
from words2macros.models import Nutrients

POTATO_PER_100G = Nutrients(calories_kcal=113, protein_g=1.9, carbs_g=17, fat_g=4.2)


def test_scale_by_grams():
    n = scale(POTATO_PER_100G, 190)

    assert n.calories_kcal == pytest.approx(214.7)
    assert n.protein_g == pytest.approx(3.61)
    assert n.carbs_g == pytest.approx(32.3)
    assert n.fat_g == pytest.approx(7.98)


def test_scale_includes_alcohol():
    tequila = Nutrients(calories_kcal=231, protein_g=0, carbs_g=0, fat_g=0, alcohol_g=33.4)

    assert scale(tequila, 45).alcohol_g == pytest.approx(15.03)


def test_scale_includes_fiber():
    assert scale(POTATO_PER_100G.model_copy(update={"fiber_g": 1.2}), 190).fiber_g == (
        pytest.approx(2.28)
    )


def test_unknown_fiber_stays_unknown():
    assert scale(POTATO_PER_100G, 190).fiber_g is None
    assert rounded(POTATO_PER_100G).fiber_g is None


def test_scale_100g_is_unchanged():
    assert scale(POTATO_PER_100G, 100) == POTATO_PER_100G


def test_total_sums_each_field():
    a = Nutrients(calories_kcal=100, protein_g=1, carbs_g=2, fat_g=3)
    b = Nutrients(calories_kcal=50, protein_g=0.5, carbs_g=0, fat_g=1)

    assert total([a, b]) == Nutrients(calories_kcal=150, protein_g=1.5, carbs_g=2, fat_g=4)


def test_total_skips_unknown_fiber():
    a = Nutrients(calories_kcal=100, protein_g=1, carbs_g=2, fat_g=3, fiber_g=1.5)
    b = Nutrients(calories_kcal=50, protein_g=0.5, carbs_g=0, fat_g=1)

    assert total([a, b]).fiber_g == 1.5


def test_total_fiber_unknown_only_when_all_unknown():
    a = Nutrients(calories_kcal=100, protein_g=1, carbs_g=2, fat_g=3)

    assert total([a, a]).fiber_g is None


def test_total_of_nothing_is_zero():
    assert total([]) == Nutrients(calories_kcal=0, protein_g=0, carbs_g=0, fat_g=0, fiber_g=0)


def test_rounded_to_one_decimal():
    n = rounded(Nutrients(calories_kcal=214.66, protein_g=3.61, carbs_g=32.34, fat_g=7.98))

    assert n == Nutrients(calories_kcal=214.7, protein_g=3.6, carbs_g=32.3, fat_g=8.0)
