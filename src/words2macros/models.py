"""Data shapes for every step of the pipeline.

Each model rejects data that does not match its shape, so nothing unvalidated
reaches the next step. Field names carry their units (grams, kcal).
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

AmountSource = Literal["stated", "estimated"]
MatchSource = Literal["usda", "ai_estimate"]
WarningCode = Literal[
    "AMOUNT_ESTIMATED",  # the AI guessed a portion size
    "CALORIE_DENSE_ESTIMATE",  # guessed portion of a calorie-dense food
    "NUTRIENTS_ESTIMATED",  # no database match; nutrients are an AI estimate
    "ENERGY_MISMATCH",  # calories far from 4P + 4C + 9F, likely a bad match
    "OVER_2000G",  # implausibly large single item
]


class StrictModel(BaseModel):
    # Reject unknown fields and treat whitespace-only text as empty.
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ParsedItem(StrictModel):
    """One food as the AI understood it from the text."""

    name: str = Field(min_length=1)
    preparation: str | None = None
    grams: float = Field(gt=0)
    amount_source: AmountSource
    assumption: str | None = None

    @model_validator(mode="after")
    def estimated_needs_assumption(self) -> "ParsedItem":
        if self.amount_source == "estimated" and not self.assumption:
            raise ValueError("an estimated amount must state its assumption")
        return self


class ParseResult(StrictModel):
    """The full AI parse output for one paragraph."""

    items: list[ParsedItem] = Field(min_length=1)


class Nutrients(StrictModel):
    calories_kcal: float = Field(ge=0)
    protein_g: float = Field(ge=0)
    carbs_g: float = Field(ge=0)
    fat_g: float = Field(ge=0)


class FoodMatch(StrictModel):
    """The food record used for an item's nutrient values."""

    source: MatchSource
    fdc_id: int | None = None
    description: str = Field(min_length=1)
    per_100g: Nutrients

    @model_validator(mode="after")
    def usda_needs_id(self) -> "FoodMatch":
        if self.source == "usda" and self.fdc_id is None:
            raise ValueError("a USDA match must include its fdc_id")
        return self


class ItemResult(StrictModel):
    name: str = Field(min_length=1)
    preparation: str | None = None
    grams: float = Field(gt=0)
    amount_source: AmountSource
    assumption: str | None = None
    match: FoodMatch
    nutrients: Nutrients


class MealWarning(StrictModel):
    """A non-fatal issue shown to the user next to the result."""

    code: WarningCode
    message: str = Field(min_length=1)
    item_index: int | None = Field(default=None, ge=0)


class MealResult(StrictModel):
    """Calculated and checked macros for one described meal."""

    items: list[ItemResult] = Field(min_length=1)
    totals: Nutrients
    warnings: list[MealWarning] = Field(default_factory=list)


class AnalyzeResponse(MealResult):
    """The POST /analyze success body: the meal result plus request details."""

    text: str  # the original input, echoed back
    request_id: str  # matches the Lambda log line for this request
    analyzed_at: datetime  # UTC
