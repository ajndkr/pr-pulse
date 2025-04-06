#!/bin/bash
set -e

if [[ "$INPUT_SHARE" == "true" && -z "$SLACK_WEBHOOK_URL" ]]; then
  echo "error: slack_webhook_url is required for sharing insights"
  exit 1
fi

if [[ "$INPUT_SHARE" == "true" ]]; then
  SHARE_FLAG="--share"
fi

pr-pulse analyze summary "$INPUT_REPOSITORY" \
  --days "$INPUT_DAYS" \
  --verbose \
  $SHARE_FLAG
