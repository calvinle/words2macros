# words2macros

Type what you ate in plain language and get back calories, protein, carbs and fat, in a
consistent structure that is verified by code.

> "I had mashed potatoes from a medium russet potato with a serving of gravy."

| Food | Amount | Database match | kcal | Protein | Carbs | Fat |
|---|---|---|---|---|---|---|
| russet potato, mashed | 202 g *(estimated: 1 medium potato)* | Potato, mashed, NFS | 230.3 | 4.3 g | 35.6 g | 8.2 g |
| gravy | 60 g *(estimated: 1 serving)* | Gravy, NFS | 31.8 | 2.2 g | 2.9 g | 1.4 g |
| **Meal total** | | | **262.1** | **6.6 g** | **38.4 g** | **9.6 g** |

Estimated amounts come back with a warning that names the assumed serving and encourages a measured
amount instead.

## Design

**The AI never produces nutrient numbers.** It only turns text into a list of foods and gram
amounts. Nutrient values come from the
[USDA FoodData Central](https://fdc.nal.usda.gov/) database, and all math is done in code.

1. **Parse (AI):** Claude (Haiku 4.5 on Amazon Bedrock) turns the paragraph into foods, preparation,
   grams, and whether each amount was *stated* or *estimated*.
2. **Match (AI-assisted):** each food is searched in USDA. Claude picks the best of the top 15
   records **by ID only**; code checks that the ID was one of the candidates. If nothing fits, Claude
   estimates nutrients, and the result is clearly labeled as an AI estimate.
3. **Calculate (code):** per-100 g values × grams, summed per item and per meal.
4. **Validate (code):** every payload is checked by a Pydantic model (see
   [Validation with Pydantic](#validation-with-pydantic)), and sanity checks add warnings:
   estimated amounts, calorie-dense estimates, calories that don't add up from the macros, and
   items over 2,000 g.

## Architecture

```
Browser ──▶ API Gateway (HTTP API) ──▶ Lambda (Python 3.13, arm64)
            POST /analyze                ├─▶ Amazon Bedrock (Claude Haiku 4.5)
            CORS, throttling             ├─▶ USDA FoodData Central API
                                         └─▶ SSM Parameter Store (USDA key, encrypted)
```

Everything is defined in [`template.yaml`](template.yaml) and deployed with AWS SAM. The Lambda
role is least-privilege: it can invoke one Bedrock model, read one SSM parameter, and write its
own logs.

## API

`POST /analyze` with `{"text": "2 scrambled eggs and a slice of toast"}`.

**200 OK** returns the meal: `items` (each with grams, `amount_source`, `assumption`, the matched
food record and its nutrients), `totals`, `warnings`, plus the original `text`, a `request_id`
and `analyzed_at` for tracing.

Errors share one shape, `{"error": {"code", "message", "request_id"}}`:

| Status | Code | Meaning |
|---|---|---|
| 400 | `INVALID_REQUEST`, `INVALID_TEXT` | malformed request, or text blank or over 2,000 characters |
| 422 | `NO_FOOD_FOUND`, `TOO_MANY_FOODS`, `UNPARSEABLE` | the text couldn't be turned into 1-10 foods |
| 502 | `MATCH_FAILED` | no usable database match or estimate |
| 503 | `NUTRITION_DB_UNAVAILABLE`, `AI_UNAVAILABLE` | USDA or Bedrock is down or busy |
| 500 | `INTERNAL_ERROR` | unexpected; details are logged, never returned |

Logs contain a request ID, timestamp, status and duration, but never the meal text.

## Project layout

```
src/words2macros/
  handler.py    Lambda entry point: HTTP in, HTTP out
  pipeline.py   analyze_meal(): parse -> match -> calculate -> validate
  parse.py      step 1, AI parsing
  match.py      step 2, USDA matching and labeled fallback
  usda.py       USDA FoodData Central client
  calculate.py  nutrient math
  checks.py     sanity-check warnings
  meal.py       builds the final MealResult
  models.py     Pydantic models
  bedrock.py    shared "ask for JSON, validate, retry once" helper
  errors.py     user-facing errors with stable codes
tests/          pytest suite; no network calls (fakes and saved USDA responses)
scripts/        run real sentences through Bedrock and USDA
```

## Local development

Requires [uv](https://docs.astral.sh/uv/), AWS credentials with Bedrock access, and a free
[USDA API key](https://fdc.nal.usda.gov/api-key-signup).

```sh
uv sync
cp .env.example .env          # then add your USDA key
uv run pytest
uv run ruff check . && uv run ruff format .
```

Try real meals (each food costs one USDA search and one Bedrock call, well under a cent):

```sh
uv run --env-file .env python scripts/try_meal.py "2 scrambled eggs and a slice of toast"
```

## Deploying

Requires the [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html).
Store the USDA key once as an encrypted parameter:

```sh
aws ssm put-parameter --name /words2macros/usda-api-key --type SecureString --value "$USDA_API_KEY"
```

Then build and deploy (SAM shows the change set and asks for confirmation):

```sh
sam build
sam deploy
```

The [`Makefile`](Makefile) is used by `sam build`: it installs the locked runtime dependencies as
Linux arm64 wheels and copies the package. `boto3` is not bundled because the Lambda runtime
already provides it. Remove everything with `sam delete`.

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
    name: str = Field(min_length=1)  # not empty (or whitespace only)
    preparation: str | None = None
    grams: float = Field(gt=0)  # must be positive
    amount_source: Literal["stated", "estimated"]  # only these two values
    assumption: str | None = None


class Nutrients(StrictModel):
    calories_kcal: float = Field(ge=0)  # no negative nutrients
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
