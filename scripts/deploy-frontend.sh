#!/usr/bin/env bash
# Build the Angular app and upload it to the site bucket created by template.yaml.
# Run from anywhere, after `sam deploy` has created the stack.
set -euo pipefail
cd "$(dirname "$0")/.."

STACK=words2macros
REGION=${AWS_REGION:-us-east-1}
DIST=frontend/dist/frontend/browser

output() {
  aws cloudformation describe-stacks --region "$REGION" --stack-name "$STACK" \
    --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" --output text
}
BUCKET=$(output SiteBucket)
URL=$(output SiteUrl)

(cd frontend && npx ng build)

# Hashed files (main-AB12CD.js) get a new name whenever their content changes,
# so browsers and CloudFront may keep them for a year.
aws s3 sync "$DIST" "s3://$BUCKET" --region "$REGION" --delete \
  --exclude index.html --exclude favicon.ico \
  --cache-control "public, max-age=31536000, immutable"

# Unhashed files keep their names, so they are always revalidated. index.html goes
# last: it points at the hashed files, which are already uploaded.
for file in favicon.ico index.html; do
  aws s3 cp "$DIST/$file" "s3://$BUCKET/$file" --region "$REGION" --cache-control "no-cache"
done

echo "Deployed to $URL"
