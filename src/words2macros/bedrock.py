"""Shared Bedrock call: ask Claude for JSON that follows a schema, then validate it in code."""

import json
import os
from collections.abc import Callable
from typing import Any

import boto3
from botocore.config import Config

MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "global.anthropic.claude-haiku-4-5-20251001-v1:0")
MAX_OUTPUT_TOKENS = 2000
ATTEMPTS = 2  # first try plus one retry, per CLAUDE.md


def make_client() -> Any:
    # Adaptive retries handle Bedrock throttling and brief outages.
    return boto3.client(
        "bedrock-runtime", config=Config(retries={"max_attempts": 5, "mode": "adaptive"})
    )


def ask_validated[T](
    client: Any,
    *,
    system: str,
    text: str,
    schema: dict[str, Any],
    schema_name: str,
    validate: Callable[[Any], T],
) -> T | None:
    """Ask the model, validate its JSON reply, and retry once on a bad reply.

    `validate` turns the decoded JSON into a result, raising ValueError (which
    includes Pydantic's ValidationError) to reject it. Returns None if both
    attempts are rejected. Other exceptions from `validate` propagate unchanged.
    """
    for _ in range(ATTEMPTS):
        reply = ask_json(client, system=system, text=text, schema=schema, schema_name=schema_name)
        try:
            return validate(json.loads(reply))
        except ValueError:  # also covers json.JSONDecodeError
            continue
    return None


def ask_json(
    client: Any, *, system: str, text: str, schema: dict[str, Any], schema_name: str
) -> str:
    response = client.converse(
        modelId=MODEL_ID,
        system=[{"text": system}],
        messages=[{"role": "user", "content": [{"text": text}]}],
        inferenceConfig={"maxTokens": MAX_OUTPUT_TOKENS, "temperature": 0},
        outputConfig={
            "textFormat": {
                "type": "json_schema",
                "structure": {
                    "jsonSchema": {"name": schema_name, "schema": json.dumps(schema)},
                },
            }
        },
    )
    return response["output"]["message"]["content"][0]["text"]
