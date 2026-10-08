# Food Macro App

Proof-of-concept web app: the user types what they ate in plain language and gets back macronutrients (protein, carbs, fat, calories) in a consistent, code-validated format that later logic can build on.

Example input: "I had mashed potatoes from a medium russet potato with a serving of gravy."

## Requirements (from the project owner)

- Input is a free-text paragraph describing food eaten.
- When amounts are given, use them for exact calculations.
- When amounts are missing, an AI system estimates the portions.
- Output has a consistent structure that is verified by code before being used for further logic.
- Hosted on AWS.
- Web application, proof of concept. Keep it simple.

## Design (confirmed)

Core rule: the AI never produces nutrient numbers. It only turns text into a structured list of foods and gram amounts. Nutrient values come from a real database, and the math is done in code.

Pipeline:

1. Parse (AI): paragraph -> list of items with name, preparation, grams, and whether the amount was stated or estimated.
2. Match (code): search each item in a nutrition database to get a specific food record.
3. Calculate (code): per-100 g nutrient values x grams, summed per item and per meal.
4. Validate (code): schema check plus sanity rules before anything is returned.

AI output shape for step 1:

```json
{
  "items": [
    {
      "name": "russet potato",
      "preparation": "mashed",
      "grams": 190,
      "amount_source": "estimated",
      "assumption": "1 medium russet"
    }
  ]
}
```

`amount_source` is "stated" or "estimated". Keep this flag all the way through to the final output.

Volume amounts ("1 cup of rice") count as "stated": the AI converts them to grams and shows the conversion in `assumption`.

Validation rules:

- Pydantic models for every payload; required fields, correct types, no negative numbers.
- Energy check: calories should be close to 4 x protein + 4 x carbs + 9 x fat. A large gap suggests a bad database match.
- Plausibility: flag any single item over 2,000 g.
- On failure: retry the AI call once, then return a clear error. Never pass unvalidated data downstream.
- Schema failures are errors. Sanity checks (energy gap, over 2,000 g) are warnings: the result is still returned with the flag shown.
- Estimates must be visible to the user. For every estimated amount, tell them the assumed serving, encourage precise measurements for accuracy, and ask them to double check their input.
- Counts and sizes ("2 eggs", "a medium potato") are "estimated". Estimated portions of calorie-dense foods (250 kcal per 100 g or more) get an extra warning, since size differences change the total more.
- User-facing messages use a neutral voice, never first person ("An estimated 190 g of mashed potato was used...", not "We assumed...").

AWS services:

- Frontend: S3 + CloudFront, or Amplify Hosting
- API: API Gateway + one Python Lambda
- AI parsing: Amazon Bedrock with structured outputs (JSON schema enforced)
- Storage: DynamoDB (meal logs, cached food lookups)
- Secrets: Secrets Manager or SSM Parameter Store

Later (not in the proof of concept): Cognito for login.

Nutrition data: USDA FoodData Central API (free data.gov key, 1,000 requests/hour, public domain).

## Known hard parts

- Database matching: "mashed potatoes" returns many records. Idea: have the AI choose the best match from the top 5 search results.
- Raw vs cooked: the gram amount and the database record must refer to the same state.
- Foods missing from the database need a fallback: an AI estimate, clearly labeled as an estimate.
- Portion estimates from text can be off by 20-30%. The output must show which numbers are estimates.

## Decisions

- Output: macros per meal, with per-item detail. Later logic (daily totals, targets) is undecided and can build on per-meal results.
- No login for the proof of concept.
- Frontend: Angular, in `frontend/`. The project is a portfolio demo for job interviews, and the owner is new to Angular.

## Development environment

- OS: Bazzite (Fedora Atomic, read-only system). Do not use `sudo dnf install` or `rpm-ostree` for project tools.
- Install command-line tools with Homebrew (`brew install ...`).
- Python: use `uv` for Python versions, virtual environments, and dependencies.
- AWS tooling: `awscli` and `aws-sam-cli` via Homebrew.
- Editor: VS Code with the Claude Code extension.

## Working style

- The project owner is new to AI development and AWS. Explain what each piece does and why, briefly, as you build it.
- Build in small steps and show proposed changes before making them.
- Use regular hyphens (-) instead of em dashes in all text you write.
