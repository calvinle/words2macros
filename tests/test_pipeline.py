"""The pipeline matches foods in parallel and keeps their order."""

import json
import threading

import pytest

from words2macros.match import MatchError
from words2macros.models import FoodMatch, Nutrients
from words2macros.pipeline import analyze_meal

FOODS = ["apple", "banana", "cherry"]

PARSE_REPLY = json.dumps(
    {
        "items": [
            {"name": f, "preparation": None, "grams": 100, "amount_source": "stated"} for f in FOODS
        ]
    }
)


class RoutingBedrock:
    """Answers by request type, since parallel match calls arrive in any order."""

    def converse(self, **request):
        schema_name = request["outputConfig"]["textFormat"]["structure"]["jsonSchema"]["name"]
        if schema_name == "meal_parse":
            text = PARSE_REPLY
        else:  # food_match: pick the first candidate
            records = json.loads(request["messages"][0]["content"][0]["text"])["records"]
            text = json.dumps({"fdc_id": records[0]["fdc_id"]})
        return {"output": {"message": {"content": [{"text": text}]}}}


def record(name: str) -> FoodMatch:
    return FoodMatch(
        source="usda",
        fdc_id=FOODS.index(name) + 1,
        description=name.title(),
        per_100g=Nutrients(calories_kcal=50, protein_g=1, carbs_g=11, fat_g=0.2),
    )


def test_foods_are_matched_at_the_same_time():
    # Every search waits until all three have started. Run one at a time,
    # the first would wait forever and the barrier would time out.
    barrier = threading.Barrier(len(FOODS), timeout=5)

    def search(query: str) -> list[FoodMatch]:
        barrier.wait()
        return [record(query)]

    result = analyze_meal("an apple, a banana and a cherry", RoutingBedrock(), search)

    assert [i.match.description for i in result.items] == ["Apple", "Banana", "Cherry"]


def test_a_failed_match_fails_the_meal():
    def search(query: str) -> list[FoodMatch]:
        if query == "banana":
            raise MatchError("A database match for banana couldn't be chosen. Try again.")
        return [record(query)]

    with pytest.raises(MatchError, match="banana"):
        analyze_meal("an apple, a banana and a cherry", RoutingBedrock(), search)
