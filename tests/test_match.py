import json
from pathlib import Path

import pytest
from fakes import FakeBedrock

from words2macros.match import MatchError, match_item
from words2macros.models import ParsedItem
from words2macros.usda import parse_search_response

FIXTURES = Path(__file__).parent / "fixtures"

GRAVY = ParsedItem(name="gravy", grams=60, amount_source="estimated", assumption="1 serving")
GRAVY_NFS_ID = 2707149  # "Gravy, NFS" in the saved USDA fixture

ESTIMATE_REPLY = json.dumps(
    {
        "description": "Gravy, homemade",
        "calories_kcal": 60,
        "protein_g": 1.5,
        "carbs_g": 5,
        "fat_g": 3.5,
        "alcohol_g": 0,
        "fiber_g": 0.3,
    }
)


def fixture_search(name: str):
    """A search function that returns a saved USDA response and records queries."""
    results = parse_search_response(json.loads((FIXTURES / name).read_text()))
    queries = []

    def search(query: str):
        queries.append(query)
        return results

    search.queries = queries
    return search


def pick(fdc_id) -> str:
    return json.dumps({"fdc_id": fdc_id})


def test_fixture_has_expected_gravy_record():
    search = fixture_search("usda_search_gravy.json")

    assert {m.fdc_id: m.description for m in search("gravy")}[GRAVY_NFS_ID] == "Gravy, NFS"


def test_ai_pick_returns_usda_record_unchanged():
    search = fixture_search("usda_search_gravy.json")
    record = {m.fdc_id: m for m in search("gravy")}[GRAVY_NFS_ID]

    match = match_item(GRAVY, FakeBedrock(pick(GRAVY_NFS_ID)), search)

    assert match == record  # nutrients come from USDA, not the AI


def test_candidates_are_sent_to_model():
    client = FakeBedrock(pick(GRAVY_NFS_ID))

    match_item(GRAVY, client, fixture_search("usda_search_gravy.json"))

    sent = json.loads(client.requests[0]["messages"][0]["content"][0]["text"])
    assert sent["food"] == {"name": "gravy", "preparation": None}
    assert len(sent["records"]) == 5


def test_search_uses_preparation_and_name():
    search = fixture_search("usda_search_mashed_potatoes.json")
    potato = ParsedItem(
        name="russet potato", preparation="mashed", grams=190, amount_source="stated"
    )

    match_item(potato, FakeBedrock(pick(2709492)), search)

    assert search.queries == ["mashed russet potato"]


def test_id_not_in_candidates_is_retried():
    client = FakeBedrock(pick(999), pick(GRAVY_NFS_ID))

    match = match_item(GRAVY, client, fixture_search("usda_search_gravy.json"))

    assert match.fdc_id == GRAVY_NFS_ID
    assert len(client.requests) == 2


def test_two_invalid_picks_raise_clear_error():
    client = FakeBedrock(pick(999), "not json")

    with pytest.raises(MatchError, match="couldn't be chosen"):
        match_item(GRAVY, client, fixture_search("usda_search_gravy.json"))


def test_no_good_candidate_falls_back_to_labeled_estimate():
    client = FakeBedrock(pick(None), ESTIMATE_REPLY)

    match = match_item(GRAVY, client, fixture_search("usda_search_gravy.json"))

    assert match.source == "ai_estimate"
    assert match.fdc_id is None
    assert match.description == "Gravy, homemade"
    assert match.per_100g.calories_kcal == 60


def test_no_search_results_skips_choice_and_estimates():
    client = FakeBedrock(ESTIMATE_REPLY)

    match = match_item(GRAVY, client, fixture_search("usda_search_xqzvplorbnut.json"))

    assert match.source == "ai_estimate"
    assert len(client.requests) == 1


def test_no_results_retries_search_without_preparation():
    search = fixture_search("usda_search_xqzvplorbnut.json")
    item = ParsedItem(name="zorbnut", preparation="fried", grams=50, amount_source="stated")

    match_item(item, FakeBedrock(ESTIMATE_REPLY), search)

    assert search.queries == ["fried zorbnut", "zorbnut"]


def test_negative_estimate_is_retried():
    bad = json.dumps({**json.loads(ESTIMATE_REPLY), "fat_g": -2})
    client = FakeBedrock(bad, ESTIMATE_REPLY)

    match = match_item(GRAVY, client, fixture_search("usda_search_xqzvplorbnut.json"))

    assert match.per_100g.fat_g == 3.5
    assert len(client.requests) == 2


def test_two_bad_estimates_raise_clear_error():
    bad = json.dumps({"description": "", "calories_kcal": 1, "protein_g": 1, "carbs_g": 1})
    client = FakeBedrock(bad, bad)

    with pytest.raises(MatchError, match="couldn't be found or estimated"):
        match_item(GRAVY, client, fixture_search("usda_search_xqzvplorbnut.json"))


def test_estimate_with_more_fiber_than_carbs_is_retried():
    bad = json.dumps({**json.loads(ESTIMATE_REPLY), "fiber_g": 9})
    client = FakeBedrock(bad, ESTIMATE_REPLY)

    match = match_item(GRAVY, client, fixture_search("usda_search_xqzvplorbnut.json"))

    assert match.per_100g.fiber_g == 0.3
    assert len(client.requests) == 2
