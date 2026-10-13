import json
from pathlib import Path

import pytest

from words2macros import usda
from words2macros.models import Nutrients
from words2macros.usda import parse_search_response

FIXTURES = Path(__file__).parent / "fixtures"


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def test_parse_mashed_potatoes():
    matches = parse_search_response(load("usda_search_mashed_potatoes.json"))

    assert len(matches) == 5
    first = matches[0]
    assert first.source == "usda"
    assert first.fdc_id == 2709492
    assert first.description == "Potato, mashed, NFS"
    assert first.per_100g == Nutrients(
        calories_kcal=114, protein_g=2.15, carbs_g=17.6, fat_g=4.07, fiber_g=1.2
    )


def test_parse_reads_alcohol():
    [tequila, sunrise] = parse_search_response(load("usda_search_tequila.json"))

    assert tequila.per_100g == Nutrients(
        calories_kcal=231, protein_g=0, carbs_g=0, fat_g=0, alcohol_g=33.4, fiber_g=0
    )
    assert sunrise.per_100g.alcohol_g == 8.1


def test_missing_alcohol_means_zero():
    # The potato records have no alcohol entry at all.
    matches = parse_search_response(load("usda_search_mashed_potatoes.json"))

    assert all(m.per_100g.alcohol_g == 0 for m in matches)


def test_missing_fiber_means_unknown():
    # Some SR Legacy records, like "Gravy, CAMPBELL'S, chicken", have no fiber entry.
    data = load("usda_search_gravy.json")
    first = data["foods"][0]
    first["foodNutrients"] = [n for n in first["foodNutrients"] if n["nutrientId"] != 1079]

    [no_fiber, *rest] = parse_search_response(data)

    assert no_fiber.per_100g.fiber_g is None
    assert rest[0].per_100g.fiber_g == 0  # "Beef with gravy" reports 0, which is known


def test_record_with_more_fiber_than_carbs_is_skipped():
    data = load("usda_search_mashed_potatoes.json")
    fiber = next(n for n in data["foods"][0]["foodNutrients"] if n["nutrientId"] == 1079)
    fiber["value"] = 50

    matches = parse_search_response(data)

    assert 2709492 not in [m.fdc_id for m in matches]


def test_parse_keeps_search_order():
    matches = parse_search_response(load("usda_search_gravy.json"))

    assert [m.description for m in matches] == [
        "Biscuit with gravy",
        "Beef with gravy",
        "Chicken with gravy",
        "Gravy, beef",
        "Gravy, NFS",
    ]


def test_parse_no_results():
    assert parse_search_response(load("usda_search_xqzvplorbnut.json")) == []


def test_record_missing_a_macro_is_skipped():
    data = load("usda_search_mashed_potatoes.json")
    first = data["foods"][0]
    first["foodNutrients"] = [n for n in first["foodNutrients"] if n["nutrientId"] != 1004]

    matches = parse_search_response(data)

    assert len(matches) == 4
    assert 2709492 not in [m.fdc_id for m in matches]


@pytest.mark.parametrize("bad", [{"value": None}, {"value": -1}])
def test_record_with_bad_value_is_skipped(bad):
    data = load("usda_search_mashed_potatoes.json")
    data["foods"][0]["foodNutrients"][0].update(bad)

    assert len(parse_search_response(data)) == 4


@pytest.fixture
def fresh_key_cache():
    usda.get_api_key.cache_clear()
    yield
    usda.get_api_key.cache_clear()


def test_api_key_from_env(monkeypatch, fresh_key_cache):
    monkeypatch.setenv("USDA_API_KEY", "local-key")

    assert usda.get_api_key() == "local-key"


def test_api_key_from_ssm_is_read_once(monkeypatch, fresh_key_cache):
    calls = []

    class FakeSsm:
        def get_parameter(self, **kwargs):
            calls.append(kwargs)
            return {"Parameter": {"Value": "ssm-key"}}

    monkeypatch.delenv("USDA_API_KEY", raising=False)
    monkeypatch.setenv("USDA_API_KEY_PARAMETER", "/words2macros/usda-api-key")
    monkeypatch.setattr(usda.boto3, "client", lambda service: FakeSsm())

    assert usda.get_api_key() == "ssm-key"
    assert usda.get_api_key() == "ssm-key"
    assert calls == [{"Name": "/words2macros/usda-api-key", "WithDecryption": True}]


def test_api_key_sent_as_header_not_in_url(monkeypatch):
    sent = []

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return (FIXTURES / "usda_search_gravy.json").read_bytes()

    def fake_urlopen(request, timeout):
        sent.append(request)
        return FakeResponse()

    monkeypatch.setattr(usda.urllib.request, "urlopen", fake_urlopen)

    matches = usda.search_foods("gravy", api_key="secret-key")

    [request] = sent
    assert request.get_header("X-api-key") == "secret-key"
    assert "secret-key" not in request.full_url
    assert len(matches) == 5
