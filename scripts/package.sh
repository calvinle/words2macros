#!/usr/bin/env bash
# Build a Lambda deployment zip at dist/lambda.zip.
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON_VERSION="$(cat .python-version)"
PLATFORM="${LAMBDA_PLATFORM:-x86_64-manylinux2014}"  # use aarch64-manylinux2014 for arm64

rm -rf build dist
mkdir -p build dist

uv export --frozen --no-dev --no-editable -o build/requirements.txt
uv pip install \
    --no-installer-metadata \
    --no-compile-bytecode \
    --python-platform "$PLATFORM" \
    --python "$PYTHON_VERSION" \
    --target build/package \
    -r build/requirements.txt

(cd build/package && zip -qr ../../dist/lambda.zip .)
echo "Built dist/lambda.zip (handler: words2macros.handler.lambda_handler)"
