#!/bin/bash
set -e

if [[ "$INPUT_COMMAND" == "detail" && -z "$INPUT_PR_NUMBER" ]]; then
  echo "error: pr_number is required for detail command"
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
else
  pr-pulse summary "$INPUT_REPOSITORY" \
    --days "$INPUT_DAYS" \
    --format "$INPUT_OUTPUT_FORMAT" \
    $VERBOSE_FLAG \
    $WRITE_FLAG
fi
