#!/bin/bash
set -euo pipefail

# ============================================================
# Runner for HLE agent comparison.
# Runs:
# 1. Direct Agent
# 2. Feedback Agent
# 3. Tool Agent
# 4. Oracle Feedback Agent
# Then summarizes accuracy.
# ============================================================

PROJECT_ROOT="/storage/homefs/mj24z011/hle-qwen-agent"
cd "${PROJECT_ROOT}"

MODEL_NAME="Qwen/Qwen2.5-7B-Instruct"
LIMIT=2000
MAX_ITERATIONS=3
TEXT_ONLY=1

OUTPUT_DIR="outputs"
DIRECT_OUTPUT="${OUTPUT_DIR}/direct_results.jsonl"
FEEDBACK_OUTPUT="${OUTPUT_DIR}/feedback_results.jsonl"
TOOL_OUTPUT="${OUTPUT_DIR}/tool_results.jsonl"
ORACLE_FEEDBACK_OUTPUT="${OUTPUT_DIR}/oracle_feedback_results.jsonl"
ORACLE_TOOL_OUTPUT="${OUTPUT_DIR}/oracle_tool_results.jsonl"
SUMMARY_OUTPUT="${OUTPUT_DIR}/summary.md"

export TAVILY_API_KEY="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"


mkdir -p "${OUTPUT_DIR}"

echo "============================================================"
echo "HLE Agent Experiment"
echo "============================================================"
echo "PROJECT_ROOT            = ${PROJECT_ROOT}"
echo "MODEL_NAME              = ${MODEL_NAME}"
echo "LIMIT                   = ${LIMIT}"
echo "MAX_ITERATIONS          = ${MAX_ITERATIONS}"
echo "TEXT_ONLY               = ${TEXT_ONLY}"
echo "OUTPUT_DIR              = ${OUTPUT_DIR}"
echo "DIRECT_OUTPUT           = ${DIRECT_OUTPUT}"
echo "FEEDBACK_OUTPUT         = ${FEEDBACK_OUTPUT}"
echo "TOOL_OUTPUT             = ${TOOL_OUTPUT}"
echo "ORACLE_FEEDBACK_OUTPUT  = ${ORACLE_FEEDBACK_OUTPUT}"
echo "SUMMARY_OUTPUT          = ${SUMMARY_OUTPUT}"
echo "============================================================"

export MODEL_NAME="${MODEL_NAME}"

TEXT_ONLY_FLAG=""
if [ "${TEXT_ONLY}" = "1" ]; then
  TEXT_ONLY_FLAG="--text-only"
fi

echo
#echo "Checking dataset..."
#python scripts/check_dataset.py \
#  --limit "${LIMIT}" \
#  ${TEXT_ONLY_FLAG}
#
#echo
#echo "Running Direct Agent..."
#python scripts/run_agents.py \
#  --agent direct \
#  --limit "${LIMIT}" \
#  ${TEXT_ONLY_FLAG} \
#  --output "${DIRECT_OUTPUT}"
#
#echo
#echo "Running Feedback Agent..."
#python scripts/run_agents.py \
#  --agent feedback \
#  --limit "${LIMIT}" \
#  ${TEXT_ONLY_FLAG} \
#  --max-iterations "${MAX_ITERATIONS}" \
#  --output "${FEEDBACK_OUTPUT}"
#
#echo
#echo "Running Tool Agent..."
#python scripts/run_agents.py \
#  --agent tool \
#  --limit "${LIMIT}" \
#  ${TEXT_ONLY_FLAG} \
#  --max-iterations "${MAX_ITERATIONS}" \
#  --output "${TOOL_OUTPUT}"
#
#echo
echo "Running Oracle Feedback Agent..."
python scripts/run_agents.py \
  --agent oracle_feedback \
  --limit "${LIMIT}" \
  ${TEXT_ONLY_FLAG} \
  --max-iterations "${MAX_ITERATIONS}" \
  --output "${ORACLE_FEEDBACK_OUTPUT}"

echo

#echo "Running Oracle Tool Agent..."
#python scripts/run_agents.py \
#  --agent oracle_tool \
#  --limit "${LIMIT}" \
#  ${TEXT_ONLY_FLAG} \
#  --max-iterations "${MAX_ITERATIONS}" \
#  --output "${ORACLE_TOOL_OUTPUT}"
#
#echo
echo "Summarizing results..."
python scripts/summarize_results.py \
  --input \
    "${DIRECT_OUTPUT}" \
    "${FEEDBACK_OUTPUT}" \
    "${TOOL_OUTPUT}" \
    "${ORACLE_FEEDBACK_OUTPUT}" \
    "${ORACLE_TOOL_OUTPUT}" \
  --output "${SUMMARY_OUTPUT}"

echo
echo "============================================================"
echo "All experiments finished."
echo "Summary saved to: ${SUMMARY_OUTPUT}"
echo "============================================================"