#!/bin/bash
set -euo pipefail

# ============================================================
# Local debug runner for HLE feedback comparison.
# Combo 1:
#   Solver model: Qwen2.5-0.5B-Instruct
#   Critic model: Qwen2.5-1.5B-Instruct
#
# Runs:
# 1. Direct Agent
# 2. Feedback Agent
# 3. Strong Feedback Agent
# 4. Oracle Feedback Agent
# 5. Tool Agent
# Then summarizes accuracy.
# ============================================================

# If PROJECT_ROOT is already set, use it.
# Otherwise, use the current working directory.
# This script is located in: <project_root>/jobs/

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"
echo "PROJECT_ROOT = ${PROJECT_ROOT}"

MODEL_NAME="Qwen/Qwen2.5-1.5B-Instruct"
CRITIC_MODEL_NAME="Qwen/Qwen2.5-3B-Instruct"
LIMIT=100
MAX_ITERATIONS=3
TEXT_ONLY=1

OUTPUT_DIR="outputs/local_combo1"
DIRECT_OUTPUT="${OUTPUT_DIR}/direct_0.5b_${LIMIT}.jsonl"
FEEDBACK_OUTPUT="${OUTPUT_DIR}/feedback_0.5b_${LIMIT}.jsonl"
STRONG_FEEDBACK_OUTPUT="${OUTPUT_DIR}/strong_feedback_0.5b_solver_1.5b_critic_${LIMIT}.jsonl"
ORACLE_FEEDBACK_OUTPUT="${OUTPUT_DIR}/oracle_feedback_0.5b_${LIMIT}.jsonl"
TOOL_OUTPUT="${OUTPUT_DIR}/tool_0.5b_${LIMIT}.jsonl"
SUMMARY_OUTPUT="${OUTPUT_DIR}/summary_combo1_${LIMIT}.md"

mkdir -p "${OUTPUT_DIR}"

export MODEL_NAME="${MODEL_NAME}"
export CRITIC_MODEL_NAME="${CRITIC_MODEL_NAME}"

TEXT_ONLY_FLAG=""
if [ "${TEXT_ONLY}" = "1" ]; then
  TEXT_ONLY_FLAG="--text-only"
fi

echo "============================================================"
echo "HLE Local Combo1 Experiment"
echo "============================================================"
echo "PROJECT_ROOT              = ${PROJECT_ROOT}"
echo "MODEL_NAME                = ${MODEL_NAME}"
echo "CRITIC_MODEL_NAME         = ${CRITIC_MODEL_NAME}"
echo "LIMIT                     = ${LIMIT}"
echo "MAX_ITERATIONS            = ${MAX_ITERATIONS}"
echo "TEXT_ONLY                 = ${TEXT_ONLY}"
echo "OUTPUT_DIR                = ${OUTPUT_DIR}"
echo "DIRECT_OUTPUT             = ${DIRECT_OUTPUT}"
echo "FEEDBACK_OUTPUT           = ${FEEDBACK_OUTPUT}"
echo "STRONG_FEEDBACK_OUTPUT    = ${STRONG_FEEDBACK_OUTPUT}"
echo "ORACLE_FEEDBACK_OUTPUT    = ${ORACLE_FEEDBACK_OUTPUT}"
echo "TOOL_OUTPUT               = ${TOOL_OUTPUT}"
echo "SUMMARY_OUTPUT            = ${SUMMARY_OUTPUT}"
echo "============================================================"
#
#echo
#echo "Checking dataset..."
#python scripts/check_dataset.py \
#  --limit "${LIMIT}" \
#  ${TEXT_ONLY_FLAG}

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
#echo "Running Strong Feedback Agent..."
#python scripts/run_agents.py \
#  --agent strong_feedback \
#  --limit "${LIMIT}" \
#  ${TEXT_ONLY_FLAG} \
#  --max-iterations "${MAX_ITERATIONS}" \
#  --output "${STRONG_FEEDBACK_OUTPUT}"

#echo
echo "Running Oracle Feedback Agent..."
python scripts/run_agents.py \
  --agent oracle_feedback \
  --limit "${LIMIT}" \
  ${TEXT_ONLY_FLAG} \
  --max-iterations "${MAX_ITERATIONS}" \
  --output "${ORACLE_FEEDBACK_OUTPUT}"

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
  --input \
    "${DIRECT_OUTPUT}" \
    "${FEEDBACK_OUTPUT}" \
    "${STRONG_FEEDBACK_OUTPUT}" \
    "${ORACLE_FEEDBACK_OUTPUT}" \
    "${TOOL_OUTPUT}" \
  --output "${SUMMARY_OUTPUT}"

echo
echo "============================================================"
echo "Local combo1 experiment finished."
echo "Summary saved to: ${SUMMARY_OUTPUT}"
echo "============================================================"
