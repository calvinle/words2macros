"""USDA FoodData Central search client.

Only searches the Survey (FNDDS) and SR Legacy databases, which describe generic
foods as eaten ("Potato, mashed"). Branded products are left out on purpose.
Search results list nutrients per 100 g.
"""

import functools
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

import boto3
from pydantic import ValidationError

from words2macros.errors import UserFacingError
from words2macros.models import FoodMatch, Nutrients

SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"
DATA_TYPES = ["Survey (FNDDS)", "SR Legacy"]
TIMEOUT_SECONDS = 10
ATTEMPTS = 2  # USDA is occasionally slow; retry once on timeouts and server errors
# USDA's ranking often puts dishes ("Almond chicken") above the plain food
# ("Almonds, NFS" ranks 6th), so give the AI a wide list to choose from.
DEFAULT_PAGE_SIZE = 15

# USDA nutrient IDs -> our field names. Energy 1008 is always in kcal.
NUTRIENT_IDS = {
    1008: "calories_kcal",
    1003: "protein_g",
    1005: "carbs_g",
    1004: "fat_g",
    1018: "alcohol_g",  # optional: many records leave it out, meaning 0
    1079: "fiber_g",  # optional: some SR Legacy records leave it out, meaning unknown
}


class UsdaError(UserFacingError):
    """The USDA API could not be reached or returned an error."""

    def __init__(self, message: str):
        super().__init__("NUTRITION_DB_UNAVAILABLE", message)


@functools.cache
def get_api_key() -> str:
    """USDA_API_KEY locally (from .env); on Lambda, the SSM parameter it names.

    Cached, so Lambda reads SSM once per cold start rather than on every request.
    """
    if key := os.environ.get("USDA_API_KEY"):
        return key
    ssm = boto3.client("ssm")
    response = ssm.get_parameter(Name=os.environ["USDA_API_KEY_PARAMETER"], WithDecryption=True)
    return response["Parameter"]["Value"]


def search_foods(
    query: str, page_size: int = DEFAULT_PAGE_SIZE, api_key: str | None = None
) -> list[FoodMatch]:
    """Top matching food records for a query, best first. Empty if nothing matched."""
    body = json.dumps({"query": query, "dataType": DATA_TYPES, "pageSize": page_size})
    # The key goes in a header, not the URL: URLs tend to end up in proxy and server logs.
    request = urllib.request.Request(
        SEARCH_URL,
        data=body.encode(),
        headers={"Content-Type": "application/json", "X-Api-Key": api_key or get_api_key()},
        method="POST",
    )
    for attempt in range(ATTEMPTS):
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                return parse_search_response(json.load(response))
        except urllib.error.HTTPError as e:
            retryable = e.code == 429 or e.code >= 500
            if not retryable or attempt == ATTEMPTS - 1:
                raise UsdaError(
                    f"The USDA nutrition database returned an error ({e.code})."
                ) from None
        except (urllib.error.URLError, TimeoutError):
            if attempt == ATTEMPTS - 1:
                raise UsdaError(
                    "The USDA nutrition database is not responding. Try again in a moment."
                ) from None
    raise AssertionError("unreachable")


def parse_search_response(data: dict[str, Any]) -> list[FoodMatch]:
    """Turn a search response into FoodMatch records, skipping incomplete ones."""
    matches = []
    for food in data.get("foods", []):
        values = {
            NUTRIENT_IDS[n["nutrientId"]]: n["value"]
            for n in food.get("foodNutrients", [])
            if n.get("nutrientId") in NUTRIENT_IDS and n.get("value") is not None
        }
        try:
            matches.append(
                FoodMatch(
                    source="usda",
                    fdc_id=food["fdcId"],
                    description=food["description"],
                    per_100g=Nutrients(**values),
                )
            )
        except (KeyError, ValidationError):
            continue  # missing a macro or malformed; not usable for calculation
    return matches
