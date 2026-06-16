#!/bin/bash
set -euo pipefail

# ============================================================
# Summarizes accuracy.
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"
echo "PROJECT_ROOT = ${PROJECT_ROOT}"

OUTPUT_DIR="outputs/three_model_comparison/qwen35_27b"
DIRECT_OUTPUT="${OUTPUT_DIR}/direct_results.jsonl"
FEEDBACK_OUTPUT="${OUTPUT_DIR}/feedback_results.jsonl"
TOOL_OUTPUT="${OUTPUT_DIR}/tool_results.jsonl"
ORACLE_FEEDBACK_OUTPUT="${OUTPUT_DIR}/oracle_feedback_results.jsonl"
ORACLE_TOOL_OUTPUT="${OUTPUT_DIR}/oracle_tool_results.jsonl"
TOOL_SEARCH_OUTPUT="${OUTPUT_DIR}/tool_search_results.jsonl"
SUMMARY_OUTPUT="${OUTPUT_DIR}/summary.md"

echo "Summarizing results..."
python scripts/summarize_results.py \
  --input \
    "${DIRECT_OUTPUT}" \
    "${FEEDBACK_OUTPUT}" \
    "${TOOL_OUTPUT}" \
    "${ORACLE_FEEDBACK_OUTPUT}" \
    "${ORACLE_TOOL_OUTPUT}" \
    "${TOOL_SEARCH_OUTPUT}" \
  --output "${SUMMARY_OUTPUT}"

echo
echo "============================================================"
echo "All experiments finished."
echo "Summary saved to: ${SUMMARY_OUTPUT}"
echo "============================================================"