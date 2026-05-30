#!/bin/bash
set -euo pipefail

# ============================================================
# Local runner for HLE agent comparison.
# Runs:
# 1. Direct Agent
# 2. Feedback Agent
# 3. Tool Agent
# Then summarizes accuracy.
# ============================================================

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "${PROJECT_ROOT}"

MODEL_NAME="Qwen/Qwen2.5-0.5B-Instruct"
LIMIT=50
MAX_ITERATIONS=2
TEXT_ONLY=1

OUTPUT_DIR="outputs"
DIRECT_OUTPUT="${OUTPUT_DIR}/direct_results.jsonl"
FEEDBACK_OUTPUT="${OUTPUT_DIR}/feedback_results.jsonl"
TOOL_OUTPUT="${OUTPUT_DIR}/tool_results.jsonl"

mkdir -p "${OUTPUT_DIR}"

echo "============================================================"
echo "HLE Agent Experiment - Local"
echo "============================================================"
echo "PROJECT_ROOT     = ${PROJECT_ROOT}"
echo "MODEL_NAME       = ${MODEL_NAME}"
echo "LIMIT            = ${LIMIT}"
echo "MAX_ITERATIONS   = ${MAX_ITERATIONS}"
echo "TEXT_ONLY        = ${TEXT_ONLY}"
echo "OUTPUT_DIR       = ${OUTPUT_DIR}"
echo "============================================================"

export MODEL_NAME="${MODEL_NAME}"

TEXT_ONLY_FLAG=""
if [ "${TEXT_ONLY}" = "1" ]; then
  TEXT_ONLY_FLAG="--text-only"
fi

echo
echo "Checking dataset..."
python scripts/check_dataset.py \
  --limit 3 \
  ${TEXT_ONLY_FLAG}

echo
echo "Running Direct Agent..."
python scripts/run_agents.py \
  --agent direct \
  --limit "${LIMIT}" \
  ${TEXT_ONLY_FLAG} \
  --output "${DIRECT_OUTPUT}"

echo
echo "Running Feedback Agent..."
python scripts/run_agents.py \
  --agent feedback \
  --limit "${LIMIT}" \
  ${TEXT_ONLY_FLAG} \
  --max-iterations "${MAX_ITERATIONS}" \
  --output "${FEEDBACK_OUTPUT}"

echo
echo "Running Tool Agent..."
python scripts/run_agents.py \
  --agent tool \
  --limit "${LIMIT}" \
  ${TEXT_ONLY_FLAG} \
  --max-iterations "${MAX_ITERATIONS}" \
  --output "${TOOL_OUTPUT}"

echo
echo "Summarizing results..."
python scripts/summarize_results.py \
  --input "${DIRECT_OUTPUT}" "${FEEDBACK_OUTPUT}" "${TOOL_OUTPUT}" \
  --output outputs/summary.md

echo
echo "============================================================"
echo "All local experiments finished."
echo "============================================================"