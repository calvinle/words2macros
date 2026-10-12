import json

import pytest
from fakes import FakeBedrock

from words2macros.models import MAX_ITEMS_PER_MEAL
from words2macros.parse import ParseError, parse_meal

GOOD_REPLY = json.dumps(
    {
        "items": [
            {
                "name": "russet potato",
                "preparation": "mashed",
                "grams": 190,
                "amount_source": "estimated",
                "assumption": "1 medium russet potato",
            },
            {
                "name": "beef gravy",
                "preparation": None,
                "grams": 60,
                "amount_source": "estimated",
                "assumption": "1 serving, about 1/4 cup",
            },
        ]
    }
)

# Valid JSON, but fails ParseResult: estimated without an assumption.
INVALID_REPLY = json.dumps(
    {
        "items": [
            {
                "name": "toast",
                "preparation": None,
                "grams": 30,
                "amount_source": "estimated",
                "assumption": None,
            }
        ]
    }
)


def test_good_reply_is_parsed():
    client = FakeBedrock(GOOD_REPLY)

    result = parse_meal("mashed potatoes with gravy", client)

    assert [i.name for i in result.items] == ["russet potato", "beef gravy"]
    assert len(client.requests) == 1


def test_request_sets_max_tokens_and_schema():
    client = FakeBedrock(GOOD_REPLY)

    parse_meal("mashed potatoes with gravy", client)

    request = client.requests[0]
    assert request["inferenceConfig"]["maxTokens"] > 0
    assert request["outputConfig"]["textFormat"]["type"] == "json_schema"
    assert request["messages"][0]["content"][0]["text"] == "mashed potatoes with gravy"


@pytest.mark.parametrize("bad_reply", ["not json", INVALID_REPLY])
def test_bad_reply_is_retried_once(bad_reply):
    client = FakeBedrock(bad_reply, GOOD_REPLY)

    result = parse_meal("mashed potatoes with gravy", client)

    assert len(result.items) == 2
    assert len(client.requests) == 2


def test_two_bad_replies_raise_clear_error():
    client = FakeBedrock("not json", INVALID_REPLY)

    with pytest.raises(ParseError, match="couldn't be understood"):
        parse_meal("mashed potatoes with gravy", client)
    assert len(client.requests) == 2


def test_no_food_found_is_not_retried():
    client = FakeBedrock(json.dumps({"items": []}))

    with pytest.raises(ParseError, match="No foods were found"):
        parse_meal("hello there", client)
    assert len(client.requests) == 1


@pytest.mark.parametrize("text", ["", "   ", "x" * 2001])
def test_bad_input_rejected_before_calling_model(text):
    client = FakeBedrock()

    with pytest.raises(ParseError):
        parse_meal(text, client)
    assert client.requests == []


def test_too_many_foods_is_rejected_without_retry():
    food = {
        "name": "grape",
        "preparation": None,
        "grams": 5,
        "amount_source": "stated",
        "assumption": None,
    }
    client = FakeBedrock(json.dumps({"items": [food] * (MAX_ITEMS_PER_MEAL + 1)}))

    with pytest.raises(ParseError, match=f"more than {MAX_ITEMS_PER_MEAL} foods") as error:
        parse_meal("sixteen grapes, one at a time", client)
    assert error.value.code == "TOO_MANY_FOODS"
    assert len(client.requests) == 1


def test_max_foods_is_allowed():
    food = {
        "name": "grape",
        "preparation": None,
        "grams": 5,
        "amount_source": "stated",
        "assumption": None,
    }

    reply = json.dumps({"items": [food] * MAX_ITEMS_PER_MEAL})
    result = parse_meal("fifteen grapes", FakeBedrock(reply))

    assert len(result.items) == MAX_ITEMS_PER_MEAL
