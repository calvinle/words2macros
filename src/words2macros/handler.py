"""AWS Lambda entry point for POST /analyze (API Gateway HTTP API).

Deliberately thin: translate the HTTP request into an analyze_meal call and the
result or error back into an HTTP response. All logic lives in the pipeline.
CORS is handled by API Gateway, not here.
"""

import base64
import binascii
import functools
import json
import logging
import os
import time
import traceback
import uuid
from datetime import UTC, datetime
from typing import Any

from botocore.exceptions import BotoCoreError, ClientError

from words2macros.bedrock import make_client
from words2macros.errors import UserFacingError
from words2macros.models import AnalyzeResponse
from words2macros.pipeline import analyze_meal

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

STATUS_BY_CODE = {
    "INVALID_REQUEST": 400,
    "INVALID_TEXT": 400,
    "NO_FOOD_FOUND": 422,
    "TOO_MANY_FOODS": 422,
    "UNPARSEABLE": 422,
    "MATCH_FAILED": 502,
    "NUTRITION_DB_UNAVAILABLE": 503,
    "AI_UNAVAILABLE": 503,
    "INTERNAL_ERROR": 500,
}

# Bedrock errors that mean "busy or briefly down", as opposed to a setup problem.
BEDROCK_UNAVAILABLE = {
    "ThrottlingException",
    "ServiceUnavailableException",
    "ModelTimeoutException",
    "ModelNotReadyException",
    "InternalServerException",
}

AI_UNAVAILABLE_MESSAGE = "The AI service is busy or unavailable. Try again in a moment."
INTERNAL_ERROR_MESSAGE = "Something went wrong. Try again later."
INVALID_REQUEST_MESSAGE = "The request must be JSON with a 'text' field."

# True until this Lambda instance has handled its first request. Cold requests also
# create the Bedrock client and read the USDA key from SSM, so they run slower.
_cold_start = True


@functools.cache
def get_client() -> Any:
    """One Bedrock client per Lambda instance, reused across requests."""
    return make_client()


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    global _cold_start
    started = time.monotonic()
    analyzed_at = datetime.now(UTC)
    request_id = getattr(context, "aws_request_id", None) or str(uuid.uuid4())
    log: dict[str, Any] = {"cold_start": _cold_start}
    _cold_start = False
    timings: dict[str, int] = {}  # parse_ms, match_ms

    try:
        text = read_text(event)
        meal = analyze_meal(text, get_client(), timings=timings)
        body = AnalyzeResponse(
            **meal.model_dump(), text=text, request_id=request_id, analyzed_at=analyzed_at
        ).model_dump(mode="json")
        status, code = 200, None
        log["items"] = len(meal.items)
        log["warnings"] = [w.code for w in meal.warnings]
    except UserFacingError as e:
        code, message = e.code, e.message
    except ClientError as e:
        aws_code = e.response.get("Error", {}).get("Code", "")
        log["aws_error"] = aws_code
        if aws_code in BEDROCK_UNAVAILABLE:
            code, message = "AI_UNAVAILABLE", AI_UNAVAILABLE_MESSAGE
        else:
            code, message = "INTERNAL_ERROR", INTERNAL_ERROR_MESSAGE
    except BotoCoreError as e:  # network-level failures reaching Bedrock
        log["aws_error"] = type(e).__name__
        code, message = "AI_UNAVAILABLE", AI_UNAVAILABLE_MESSAGE
    except Exception as e:
        # Log the type and stack only: exception messages (e.g. Pydantic errors)
        # can contain pieces of the meal text, which is never logged.
        log["error_type"] = type(e).__name__
        log["stack"] = traceback.format_tb(e.__traceback__)
        code, message = "INTERNAL_ERROR", INTERNAL_ERROR_MESSAGE

    log.update(timings)
    if code is not None:
        status = STATUS_BY_CODE[code]
        body = {"error": {"code": code, "message": message, "request_id": request_id}}

    logger.info(
        json.dumps(
            {
                "request_id": request_id,
                "timestamp": analyzed_at.isoformat(),
                "status": status,
                "code": code,
                "duration_ms": round((time.monotonic() - started) * 1000),
                **log,
            }
        )
    )
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def read_text(event: dict[str, Any]) -> str:
    """The 'text' field from the request body, or an INVALID_REQUEST error."""
    raw = event.get("body")
    if not isinstance(raw, str):
        raise UserFacingError("INVALID_REQUEST", INVALID_REQUEST_MESSAGE)
    try:
        if event.get("isBase64Encoded"):
            raw = base64.b64decode(raw, validate=True).decode("utf-8")
        data = json.loads(raw)
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError):
        raise UserFacingError("INVALID_REQUEST", INVALID_REQUEST_MESSAGE) from None
    if not isinstance(data, dict) or not isinstance(data.get("text"), str):
        raise UserFacingError("INVALID_REQUEST", INVALID_REQUEST_MESSAGE)
    return data["text"]
