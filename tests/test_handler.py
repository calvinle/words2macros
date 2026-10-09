import base64
import json
import logging
from types import SimpleNamespace

import pytest
from botocore.exceptions import ClientError, EndpointConnectionError

from words2macros import handler
from words2macros.match import MatchError
from words2macros.meal import build_meal_result
from words2macros.models import FoodMatch, MealResult, ParsedItem
from words2macros.parse import ParseError
from words2macros.usda import UsdaError

TEXT = "2 eggs and a slice of toast"
CONTEXT = SimpleNamespace(aws_request_id="req-123")

EGGS = ParsedItem(name="egg", grams=100, amount_source="estimated", assumption="2 eggs")
EGG_MATCH = FoodMatch(
    source="usda",
    fdc_id=1,
    description="Egg, whole, cooked",
    per_100g={"calories_kcal": 149, "protein_g": 10, "carbs_g": 1.6, "fat_g": 11},
)
MEAL: MealResult = build_meal_result([(EGGS, EGG_MATCH)])


def event(body, base64_encoded=False) -> dict:
    if isinstance(body, dict):
        body = json.dumps(body)
    if base64_encoded:
        body = base64.b64encode(body.encode()).decode()
    return {"body": body, "isBase64Encoded": base64_encoded}


@pytest.fixture
def pipeline(monkeypatch):
    """Replace the real pipeline and Bedrock client; record the text received."""
    calls = []
    outcome = {"result": MEAL}

    def fake_analyze(text, client):
        calls.append(text)
        if isinstance(outcome["result"], Exception):
            raise outcome["result"]
        return outcome["result"]

    monkeypatch.setattr(handler, "analyze_meal", fake_analyze)
    monkeypatch.setattr(handler, "get_client", lambda: None)
    return SimpleNamespace(calls=calls, outcome=outcome)


def call(evt) -> tuple[int, dict]:
    response = handler.lambda_handler(evt, CONTEXT)
    assert response["headers"]["Content-Type"] == "application/json"
    return response["statusCode"], json.loads(response["body"])


def test_success_returns_meal_with_request_details(pipeline):
    status, body = call(event({"text": TEXT}))

    assert status == 200
    assert body["text"] == TEXT
    assert body["request_id"] == "req-123"
    assert body["analyzed_at"].endswith("Z") or body["analyzed_at"].endswith("+00:00")
    assert body["totals"] == MEAL.totals.model_dump()
    assert body["items"][0]["amount_source"] == "estimated"
    assert body["warnings"][0]["code"] == "AMOUNT_ESTIMATED"
    assert pipeline.calls == [TEXT]


def test_base64_body_is_decoded(pipeline):
    status, _ = call(event({"text": TEXT}, base64_encoded=True))

    assert status == 200
    assert pipeline.calls == [TEXT]


@pytest.mark.parametrize(
    "evt",
    [
        {},
        {"body": None},
        event("not json"),
        event("[1, 2]"),
        event({"meal": TEXT}),
        event({"text": 42}),
        {"body": "%%%not base64", "isBase64Encoded": True},
    ],
    ids=["no-body", "null-body", "bad-json", "not-object", "no-text", "text-not-string", "bad-b64"],
)
def test_invalid_request(pipeline, evt):
    status, body = call(evt)

    assert status == 400
    assert body == {
        "error": {
            "code": "INVALID_REQUEST",
            "message": "The request must be JSON with a 'text' field.",
            "request_id": "req-123",
        }
    }
    assert pipeline.calls == []


@pytest.mark.parametrize(
    "error, status, code",
    [
        (ParseError("INVALID_TEXT", "The meal description is empty."), 400, "INVALID_TEXT"),
        (ParseError("NO_FOOD_FOUND", "No foods were found."), 422, "NO_FOOD_FOUND"),
        (ParseError("UNPARSEABLE", "Couldn't be understood."), 422, "UNPARSEABLE"),
        (MatchError("A match couldn't be chosen."), 502, "MATCH_FAILED"),
        (UsdaError("Not responding."), 503, "NUTRITION_DB_UNAVAILABLE"),
    ],
)
def test_user_facing_errors(pipeline, error, status, code):
    pipeline.outcome["result"] = error

    got_status, body = call(event({"text": TEXT}))

    assert got_status == status
    assert body["error"]["code"] == code
    assert body["error"]["message"] == error.message


def bedrock_error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": "x"}}, "Converse")


@pytest.mark.parametrize(
    "error",
    [bedrock_error("ThrottlingException"), EndpointConnectionError(endpoint_url="https://x")],
)
def test_bedrock_unavailable(pipeline, error):
    pipeline.outcome["result"] = error

    status, body = call(event({"text": TEXT}))

    assert status == 503
    assert body["error"]["code"] == "AI_UNAVAILABLE"


def test_bedrock_setup_problem_is_internal_error(pipeline):
    pipeline.outcome["result"] = bedrock_error("AccessDeniedException")

    status, body = call(event({"text": TEXT}))

    assert status == 500
    assert body["error"]["code"] == "INTERNAL_ERROR"


def test_unexpected_error_hides_details(pipeline):
    pipeline.outcome["result"] = ValueError(f"bad value: {TEXT}")

    status, body = call(event({"text": TEXT}))

    assert status == 500
    assert body["error"]["message"] == "Something went wrong. Try again later."
    assert TEXT not in json.dumps(body)


@pytest.mark.parametrize("fails", [False, True])
def test_log_has_timestamp_and_id_but_not_text(pipeline, caplog, fails):
    if fails:
        pipeline.outcome["result"] = ValueError(f"bad value: {TEXT}")

    with caplog.at_level(logging.INFO):
        call(event({"text": TEXT}))

    [record] = [r for r in caplog.records if r.name == "root"]
    line = json.loads(record.getMessage())
    assert line["request_id"] == "req-123"
    assert "timestamp" in line
    assert "duration_ms" in line
    assert TEXT not in record.getMessage()
