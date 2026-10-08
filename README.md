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

## Packaging

```sh
uv lock
./scripts/package.sh                                    # x86_64
LAMBDA_PLATFORM=aarch64-manylinux2014 ./scripts/package.sh  # arm64
```

Upload `dist/lambda.zip` with handler `words2macros.handler.lambda_handler` and runtime `python3.13`.
