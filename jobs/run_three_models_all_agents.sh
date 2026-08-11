#!/bin/bash
set -euo pipefail

# ============================================================
# HLE: run all selected agents on three models sequentially.
#
# Models:
#   1. Qwen3.5-0.8B            (small)
#   2. Qwen2.5-7B-Instruct     (middle / preliminary)
#   3. Qwen3.5-27B             (large)
#
# Agents:
#   direct, feedback, tool, tool_search,
#   oracle_feedback, oracle_tool
#
# Outputs:
#   outputs/three_model_comparison/<model_tag>/<agent>_results.jsonl
#
# Existing JSONL files are resumed by sample index. If a file already
# contains LIMIT non-empty records, that model/agent run is skipped.
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

#PROJECT_ROOT="/storage/homefs/mj24z011/hle-qwen-agent"
#cd "${PROJECT_ROOT}"

# ----------------------------
# Experiment configuration
# ----------------------------
MODELS=(
#  "Qwen/Qwen3.5-0.8B"
#  "Qwen/Qwen2.5-7B-Instruct"
#  "Qwen/Qwen3.5-9B"
  "Qwen/Qwen3.5-27B"
)

MODEL_TAGS=(
#  "qwen35_08b"
#  "qwen25_7b"
#  "qwen35_9b"
  "qwen35_27b"
)

AGENTS=(
#  "direct"
#  "feedback"
#  "tool"
#  "tool_search"
#  "oracle_feedback"
#  "oracle_tool"
#  "xmaster_feedback"
  "xmaster_total"
)

# All experiment parameters are intentionally fixed here.
LIMIT=1000
MAX_ITERATIONS=3
TEXT_ONLY=1
MAX_NEW_TOKENS=256
TEMPERATURE=0.0
OUTPUT_ROOT="outputs/three_model_comparison"
RUN_SCRIPT="scripts/run_agents.py"

# Tavily search settings.
TAVILY_SEARCH_NUM_RESULTS=5
TAVILY_SEARCH_DEPTH="basic"
TAVILY_SEARCH_TOPIC="general"

# 1 = resume existing JSONL files and skip files that already reached LIMIT.
# 0 = delete existing JSONL files and rerun from index 0.
RESUME_EXISTING=1

# Runtime/cache settings.
HF_HOME="${HOME}/.cache/huggingface"
TOKENIZERS_PARALLELISM=false
PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"

export TAVILY_SEARCH_NUM_RESULTS
export TAVILY_SEARCH_DEPTH
export TAVILY_SEARCH_TOPIC
export HF_HOME
export TOKENIZERS_PARALLELISM
export PYTORCH_CUDA_ALLOC_CONF
export PYTHON_PROGRAMMER_MAX_NEW_TOKENS=512
export PYTHON_VERIFIER_MAX_NEW_TOKENS=96

# Optional: load Tavily key from a private file on Ubelix.
# The file should contain:
#   export TAVILY_API_KEY="tvly-..."
if [[ -f "${HOME}/.hle_search_env" ]]; then
  # shellcheck disable=SC1090
  source "${HOME}/.hle_search_env"
fi

if [[ " ${AGENTS[*]} " == *" tool "* ]]; then
  if [[ -f "${HOME}/.hle_search_env" ]]; then
    # shellcheck disable=SC1090
    source "${HOME}/.hle_search_env"
  fi

  if [[ -z "${TAVILY_API_KEY:-}" ]]; then
    echo "ERROR: TAVILY_API_KEY is required for the tool agent."
    exit 1
  fi
fi

if [[ ! -f "${RUN_SCRIPT}" ]]; then
  echo "ERROR: ${RUN_SCRIPT} was not found."
  echo "Copy the Tavily search patch into the project first."
  exit 1
fi

mkdir -p "${OUTPUT_ROOT}"

TEXT_ONLY_FLAG=()
if [[ "${TEXT_ONLY}" == "1" ]]; then
  TEXT_ONLY_FLAG=(--text-only)
fi

run_one_agent() {
  local model_name="$1"
  local model_tag="$2"
  local agent="$3"
  local model_dir="${OUTPUT_ROOT}/${model_tag}"
  local output_file="${model_dir}/${agent}_results.jsonl"

  mkdir -p "${model_dir}"

  if [[ "${RESUME_EXISTING}" == "1" && -f "${output_file}" ]]; then
    completed_count=$(grep -cve '^[[:space:]]*$' "${output_file}" || true)

    if (( completed_count >= LIMIT )); then
      echo "[SKIP] ${model_tag} / ${agent}: ${completed_count}/${LIMIT} records already exist."
      return 0
    fi

    echo "[RESUME] ${model_tag} / ${agent}: continuing from ${completed_count}/${LIMIT} records."
  elif [[ "${RESUME_EXISTING}" == "0" && -f "${output_file}" ]]; then
    echo "[OVERWRITE] Removing existing file: ${output_file}"
    rm -f "${output_file}"
  fi

  echo
  echo "============================================================"
  echo "Model : ${model_name}"
  echo "Agent : ${agent}"
  echo "Output: ${output_file}"
  echo "============================================================"

  MODEL_NAME="${model_name}" \
  MAX_NEW_TOKENS="${MAX_NEW_TOKENS}" \
  TEMPERATURE="${TEMPERATURE}" \
  python "${RUN_SCRIPT}" \
    --agent "${agent}" \
    --limit "${LIMIT}" \
    "${TEXT_ONLY_FLAG[@]}" \
    --max-iterations "${MAX_ITERATIONS}" \
    --output "${output_file}"
}


# ----------------------------
# Run all models and agents
# ----------------------------
echo "============================================================"
echo "Three-model HLE agent experiment"
echo "============================================================"
echo "Project root   : ${PROJECT_ROOT}"
echo "Output root    : ${OUTPUT_ROOT}"
echo "Limit          : ${LIMIT}"
echo "Max iterations : ${MAX_ITERATIONS}"
echo "Text only      : ${TEXT_ONLY}"
echo "Resume existing: ${RESUME_EXISTING}"
echo "Tavily results : ${TAVILY_SEARCH_NUM_RESULTS}"
echo "Tavily depth   : ${TAVILY_SEARCH_DEPTH}"
echo "Models         : ${MODELS[*]}"
echo "Agents         : ${AGENTS[*]}"
echo "============================================================"

for i in "${!MODELS[@]}"; do
  model_name="${MODELS[$i]}"
  model_tag="${MODEL_TAGS[$i]}"

  echo
  echo "############################################################"
  echo "Starting model: ${model_name}"
  echo "############################################################"

  for agent in "${AGENTS[@]}"; do
    run_one_agent "${model_name}" "${model_tag}" "${agent}"
  done

done

echo
echo "============================================================"
echo "All requested experiments finished."
echo "JSONL outputs  : ${OUTPUT_ROOT}/<model_tag>/<agent>_results.jsonl"
echo "============================================================"
