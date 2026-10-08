"""USDA FoodData Central search client.

Only searches the Survey (FNDDS) and SR Legacy databases, which describe generic
foods as eaten ("Potato, mashed"). Branded products are left out on purpose.
Search results list nutrients per 100 g.
"""

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from pydantic import ValidationError

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
}


class UsdaError(Exception):
    """The USDA API could not be reached or returned an error. Safe to show users."""


def search_foods(
    query: str, page_size: int = DEFAULT_PAGE_SIZE, api_key: str | None = None
) -> list[FoodMatch]:
    """Top matching food records for a query, best first. Empty if nothing matched."""
    api_key = api_key or os.environ["USDA_API_KEY"]
    url = f"{SEARCH_URL}?{urllib.parse.urlencode({'api_key': api_key})}"
    body = json.dumps({"query": query, "dataType": DATA_TYPES, "pageSize": page_size})
    request = urllib.request.Request(
        url, data=body.encode(), headers={"Content-Type": "application/json"}, method="POST"
    )
    for attempt in range(ATTEMPTS):
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                return parse_search_response(json.load(response))
        except urllib.error.HTTPError as e:
            # Error messages never include the URL: it contains the API key.
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
