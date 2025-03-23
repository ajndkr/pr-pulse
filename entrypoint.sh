#!/bin/bash
set -e

if [[ "$INPUT_COMMAND" == "detail" && -z "$INPUT_PR_NUMBER" ]]; then
  echo "error: pr_number is required for detail command"
  exit 1
fi

if [[ "$INPUT_COMMAND" == "report" && -z "$GENAI_API_KEY" ]]; then
  echo "error: api_key is required for report command"
  exit 1
fi

if [[ "$INPUT_COMMAND" == "notify" && -z "$SLACK_WEBHOOK_URL" ]]; then
  echo "error: slack_webhook_url is required for notify command"
  exit 1
fi

VERBOSE_FLAG=""
if [[ "$INPUT_VERBOSE" == "true" ]]; then
  VERBOSE_FLAG="--verbose"
fi

WRITE_FLAG=""
if [[ "$INPUT_WRITE" == "true" ]]; then
  WRITE_FLAG="--write"
fi

if [[ "$INPUT_COMMAND" == "detail" ]]; then
  pr-pulse detail "$INPUT_REPOSITORY" "$INPUT_PR_NUMBER" \
    --format "$INPUT_OUTPUT_FORMAT" \
    $VERBOSE_FLAG \
    $WRITE_FLAG
elif [[ "$INPUT_COMMAND" == "list" ]]; then
  pr-pulse list "$INPUT_REPOSITORY" \
    --days "$INPUT_DAYS" \
    --format "$INPUT_OUTPUT_FORMAT" \
    $VERBOSE_FLAG \
    $WRITE_FLAG
elif [[ "$INPUT_COMMAND" == "report" ]]; then
  pr-pulse summary "$INPUT_REPOSITORY" \
    --days "$INPUT_DAYS" \
    --format json \
    --write \
    $VERBOSE_FLAG

  SUMMARY_FILE=$(find . -name 'pr-pulse-*.json')

  pr-pulse report "$SUMMARY_FILE" \
    --api-key "$GENAI_API_KEY" \
    $VERBOSE_FLAG
elif [[ "$INPUT_COMMAND" == "notify" ]]; then
  pr-pulse summary "$INPUT_REPOSITORY" \
    --days "$INPUT_DAYS" \
    --format json \
    --write \
    $VERBOSE_FLAG

  SUMMARY_FILE=$(find . -name 'pr-pulse-*.json')

  pr-pulse notify "$SUMMARY_FILE" \
    --webhook-url "$SLACK_WEBHOOK_URL" \
    $VERBOSE_FLAG
else
  pr-pulse summary "$INPUT_REPOSITORY" \
    --days "$INPUT_DAYS" \
    --format "$INPUT_OUTPUT_FORMAT" \
    $VERBOSE_FLAG \
    $WRITE_FLAG
fi
