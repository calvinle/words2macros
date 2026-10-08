"""Step 1 of the pipeline: turn a meal description into foods and gram amounts.

The AI only parses. It never returns nutrient numbers, and its reply is checked
against ParseResult before anything else uses it.
"""

import json
import os
from typing import Any

import boto3
from botocore.config import Config
from pydantic import ValidationError

from words2macros.models import ParseResult

MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "global.anthropic.claude-haiku-4-5-20251001-v1:0")
MAX_INPUT_CHARS = 2000
MAX_OUTPUT_TOKENS = 2000
ATTEMPTS = 2  # first try plus one retry, per CLAUDE.md

SYSTEM_PROMPT = """\
You turn a person's description of what they ate into a list of foods with weights in grams.

Rules:
- One item per distinct food. Keep sauces, toppings, spreads and drinks as separate items.
- name: the food in plain words a nutrition database would use, such as "russet potato" or \
"beef gravy". Do not include amounts or preparation in the name.
- preparation: how it was prepared, such as "mashed", "grilled" or "raw". Use null if unknown.
- grams: the weight of the food as eaten. For cooked food, use the cooked weight.
- amount_source:
  - "stated" when the person gave a weight (g, oz, lb) or a volume (cups, tbsp, tsp, ml). \
Convert to grams and put the conversion in assumption, for example "1 cup cooked rice = about \
185 g".
  - "estimated" otherwise, including counts and sizes ("a medium potato", "2 eggs"), vague \
amounts ("a serving", "a bowl") and no amount at all. Estimate a typical portion and describe \
it in assumption, for example "1 medium russet potato".
- assumption: a short note on how grams were decided. Required when amount_source is \
"estimated".
- Never include calories or nutrients. Only foods and amounts.
- If the text describes no food, return an empty items list.
"""

# The JSON schema the model must follow. Kept simpler than ParseResult because
# structured outputs support only part of JSON Schema; ParseResult then enforces
# the remaining rules (non-empty names, grams > 0, assumption when estimated).
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "preparation": {"type": ["string", "null"]},
                    "grams": {"type": "number"},
                    "amount_source": {"type": "string", "enum": ["stated", "estimated"]},
                    "assumption": {"type": ["string", "null"]},
                },
                "required": ["name", "preparation", "grams", "amount_source", "assumption"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["items"],
    "additionalProperties": False,
}


class ParseError(Exception):
    """The meal description could not be turned into a valid parse. Safe to show users.

    Messages use a neutral voice (no "we").
    """


def make_client() -> Any:
    # Adaptive retries handle Bedrock throttling and brief outages.
    return boto3.client(
        "bedrock-runtime", config=Config(retries={"max_attempts": 5, "mode": "adaptive"})
    )


def parse_meal(text: str, client: Any = None) -> ParseResult:
    text = text.strip()
    if not text:
        raise ParseError("The meal description is empty. Enter what was eaten.")
    if len(text) > MAX_INPUT_CHARS:
        raise ParseError(f"The meal description must be under {MAX_INPUT_CHARS:,} characters.")

    client = client or make_client()
    for _ in range(ATTEMPTS):
        reply = _ask_model(client, text)
        try:
            data = json.loads(reply)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and data.get("items") == []:
            raise ParseError(
                "No foods were found in that description. Try listing what was eaten, "
                "for example: '2 eggs and a slice of toast'."
            )
        try:
            return ParseResult.model_validate(data)
        except ValidationError:
            continue
    raise ParseError(
        "The meal description couldn't be understood. Try rephrasing it, with one food per "
        "phrase and amounts where known."
    )


def _ask_model(client: Any, text: str) -> str:
    response = client.converse(
        modelId=MODEL_ID,
        system=[{"text": SYSTEM_PROMPT}],
        messages=[{"role": "user", "content": [{"text": text}]}],
        inferenceConfig={"maxTokens": MAX_OUTPUT_TOKENS, "temperature": 0},
        outputConfig={
            "textFormat": {
                "type": "json_schema",
                "structure": {
                    "jsonSchema": {
                        "name": "meal_parse",
                        "description": "Foods and gram amounts from a meal description",
                        "schema": json.dumps(OUTPUT_SCHEMA),
                    }
                },
            }
        },
    )
    return response["output"]["message"]["content"][0]["text"]
