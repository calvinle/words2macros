"""Step 1 of the pipeline: turn a meal description into foods and gram amounts.

The AI only parses. It never returns nutrient numbers, and its reply is checked
against ParseResult before anything else uses it.
"""

from typing import Any

from words2macros.bedrock import ask_validated, make_client
from words2macros.errors import UserFacingError
from words2macros.models import MAX_ITEMS_PER_MEAL, ParseResult

MAX_INPUT_CHARS = 2000

SYSTEM_PROMPT = """\
You turn a person's description of what they ate into a list of foods with weights in grams.

Rules:
- One item per distinct food. Keep sauces, toppings, spreads and drinks as separate items.
- name: the food in plain words a nutrition database would use, such as "russet potato" or \
"gravy". Do not include amounts or preparation in the name.
- Keep the person's wording for the food. Do not add a type, flavor or variety they did not \
say: "gravy" stays "gravy", not "beef gravy"; "cheese" stays "cheese", not "cheddar cheese".
- preparation: how it was prepared, such as "mashed", "grilled", "dry" or "raw". Use null if \
unknown.
- grams and preparation must describe the same state of the food, because the preparation decides \
which database record is used:
  - If the amount is for the food before cooking ("1/2 cup dry oats", "100 g dry spaghetti", \
"1 lb raw ground beef", recipe ingredient lists), keep that state: preparation "dry" or "raw" \
and the uncooked grams. Never convert an uncooked amount to a cooked weight.
  - If the amount is for the finished food ("1 cup cooked rice", "a bowl of mashed potatoes"), \
use the cooked preparation and the cooked weight.
  - If a dish is described by its ingredient ("mashed potatoes from a medium russet potato"), \
the amount is for the ingredient: use the ingredient raw ("russet potato", "raw") with its raw \
weight. Count only foods the person mentioned. In assumption, name common additions they did \
not mention as not counted, for example "1 medium russet potato, raw weight; butter and milk \
not mentioned, not counted".
- dry_amount: true only when grams are the dry, uncooked weight of a food that absorbs water \
when cooked: dried beans, chickpeas and lentils, rice and other grains, pasta, oats. Otherwise \
false, including raw meat, raw vegetables, fruit and anything already cooked or canned.
- Leave out plain water, and black coffee or tea, when they are only used for cooking or have \
no calories.
- amount_source:
  - "stated" when the person gave a weight (g, oz, lb) or a volume (cups, tbsp, tsp, ml). \
Convert to grams and put the conversion in assumption, for example "1 cup cooked rice = about \
185 g".
  - Convert volumes with the weight of that food, not of water. 1 cup is about 240 g only \
for water-like liquids (milk, juice, broth); for example 1 cup cooked rice = about 185 g, \
1 cup raw spinach = about 30 g.
  - Canned foods packed in liquid (beans, chickpeas, vegetables, fruit, tuna) count drained: \
preparation "canned, drained" and the drained weight, for example "1 cup canned chickpeas, \
drained = about 150 g". A can of beans is about 250 g drained. Only if the person says they \
had the liquid too, use preparation "canned, with liquid" and the weight with the liquid.
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
                    "dry_amount": {"type": "boolean"},
                },
                "required": [
                    "name",
                    "preparation",
                    "grams",
                    "amount_source",
                    "assumption",
                    "dry_amount",
                ],
                "additionalProperties": False,
            },
        }
    },
    "required": ["items"],
    "additionalProperties": False,
}


class ParseError(UserFacingError):
    """The meal description could not be turned into a valid parse.

    Codes: INVALID_TEXT, NO_FOOD_FOUND, TOO_MANY_FOODS, UNPARSEABLE.
    """


def parse_meal(text: str, client: Any = None) -> ParseResult:
    text = text.strip()
    if not text:
        raise ParseError("INVALID_TEXT", "The meal description is empty. Enter what was eaten.")
    if len(text) > MAX_INPUT_CHARS:
        raise ParseError(
            "INVALID_TEXT", f"The meal description must be under {MAX_INPUT_CHARS:,} characters."
        )

    result = ask_validated(
        client or make_client(),
        system=SYSTEM_PROMPT,
        text=text,
        schema=OUTPUT_SCHEMA,
        schema_name="meal_parse",
        validate=_validate,
    )
    if result is None:
        raise ParseError(
            "UNPARSEABLE",
            "The meal description couldn't be understood. Try rephrasing it, with one food per "
            "phrase and amounts where known.",
        )
    return result


def _validate(data: Any) -> ParseResult:
    if isinstance(data, dict) and data.get("items") == []:
        # Not a bad reply, so don't retry: there is simply no food in the text.
        raise ParseError(
            "NO_FOOD_FOUND",
            "No foods were found in that description. Try listing what was eaten, "
            "for example: '2 eggs and a slice of toast'.",
        )
    if isinstance(data, dict) and len(data.get("items", [])) > MAX_ITEMS_PER_MEAL:
        # Also not worth retrying: the text really lists too many foods.
        raise ParseError(
            "TOO_MANY_FOODS",
            f"That description lists more than {MAX_ITEMS_PER_MEAL} foods. Split it into "
            f"smaller meals of up to {MAX_ITEMS_PER_MEAL} foods each.",
        )
    return ParseResult.model_validate(data)
