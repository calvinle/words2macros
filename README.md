# words2macros

AWS Lambda function (Python 3.13), managed with [uv](https://docs.astral.sh/uv/).

## Setup

```sh
uv sync
```

## Development

```sh
uv run pytest
uv run ruff check .
uv run ruff format .
```

Add a runtime dependency with `uv add <pkg>`, or a dev-only one with `uv add --dev <pkg>`.
`boto3` is a dev dependency because the Lambda runtime already provides it.

## Validation with Pydantic

Every payload that crosses a trust boundary (AI replies, HTTP requests, USDA data) is checked by a
[Pydantic](https://docs.pydantic.dev/) model before any other code uses it. The models live in
[`src/words2macros/models.py`](src/words2macros/models.py).

### Strict base model

All models inherit from `StrictModel`, which rejects unknown fields and trims whitespace:

```python
class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
```

`extra="forbid"` means an AI reply that adds a field nobody asked for, such as `"calories": 200`,
fails validation. This enforces the core rule that the AI never supplies nutrient numbers.

### Field rules

Constraints are declared on the fields themselves:

```python
class ParsedItem(StrictModel):
    name: str = Field(min_length=1)               # not empty (or whitespace only)
    preparation: str | None = None
    grams: float = Field(gt=0)                    # must be positive
    amount_source: Literal["stated", "estimated"] # only these two values
    assumption: str | None = None

class Nutrients(StrictModel):
    calories_kcal: float = Field(ge=0)            # no negative nutrients
    ...

class ParseResult(StrictModel):
    items: list[ParsedItem] = Field(min_length=1, max_length=MAX_ITEMS_PER_MEAL)
```

### Rules across fields

When a rule involves more than one field, a `model_validator` runs after the field checks:

```python
@model_validator(mode="after")
def estimated_needs_assumption(self) -> "ParsedItem":
    if self.amount_source == "estimated" and not self.assumption:
        raise ValueError("an estimated amount must state its assumption")
    return self
```

`FoodMatch` uses the same pattern to require an `fdc_id` whenever the source is `"usda"`.

### Where validation happens

| Step | Input | Validated by |
|---|---|---|
| Parse ([`parse.py`](src/words2macros/parse.py)) | Claude's JSON reply | `ParseResult` |
| Match ([`match.py`](src/words2macros/match.py)) | the record ID Claude picked, or its fallback estimate | ID checked against the candidates sent; estimate built as a `FoodMatch` |
| USDA lookup ([`usda.py`](src/words2macros/usda.py)) | search results | `FoodMatch` / `Nutrients`; incomplete records are skipped |
| Result ([`meal.py`](src/words2macros/meal.py)) | calculated totals and warnings | `MealResult` |
| API response ([`handler.py`](src/words2macros/handler.py)) | the final body | `AnalyzeResponse` |

Bedrock's structured outputs enforce the basic JSON shape of every AI reply. Pydantic then enforces
the rules a JSON schema can't express, such as the assumption rule above.

### When validation fails

[`bedrock.py`](src/words2macros/bedrock.py) asks the model again once if a reply fails validation
(`ValidationError` is a `ValueError`, which `ask_validated` catches). If the second reply also
fails, the user gets a clear error such as `UNPARSEABLE` (HTTP 422). Unvalidated data never reaches
the calculations or the response.

## Packaging

```sh
uv lock
./scripts/package.sh                                    # x86_64
LAMBDA_PLATFORM=aarch64-manylinux2014 ./scripts/package.sh  # arm64
```

Upload `dist/lambda.zip` with handler `words2macros.handler.lambda_handler` and runtime `python3.13`.
