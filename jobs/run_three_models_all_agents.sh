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
#   outputs/three_model_comparison/<model_tag>/summary.md
#   outputs/three_model_comparison/overall_comparison.md
#   outputs/three_model_comparison/overall_comparison.csv
# ============================================================

PROJECT_ROOT="/storage/homefs/mj24z011/hle-qwen-agent"
cd "${PROJECT_ROOT}"

# ----------------------------
# Experiment configuration
# ----------------------------
MODELS=(
#  "Qwen/Qwen3.5-0.8B"
#  "Qwen/Qwen2.5-7B-Instruct"
  "Qwen/Qwen3.5-27B"
)

MODEL_TAGS=(
#  "qwen35_08b"
#  "qwen25_7b"
  "qwen35_27b"
)

AGENTS=(
  "direct"
#  "feedback"
#  "tool"
#  "tool_search"
#  "oracle_feedback"
#  "oracle_tool"
)

# All experiment parameters are intentionally fixed here.
LIMIT=200
MAX_ITERATIONS=3
TEXT_ONLY=1
MAX_NEW_TOKENS=64
TEMPERATURE=0.0
OUTPUT_ROOT="outputs/three_model_comparison"
RUN_SCRIPT="scripts/run_agents.py"

# Quantization:
# "auto" means only the 27B model is loaded in NF4 4-bit.
LOAD_IN_4BIT="auto"

# Tavily search settings.
TAVILY_SEARCH_NUM_RESULTS=5
TAVILY_SEARCH_DEPTH="basic"
TAVILY_SEARCH_TOPIC="general"

# 1 = skip a non-empty result file; 0 = overwrite all results.
SKIP_EXISTING=1

# Runtime/cache settings.
HF_HOME="${HOME}/.cache/huggingface"
TOKENIZERS_PARALLELISM=false
PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"

export LOAD_IN_4BIT
export TAVILY_SEARCH_NUM_RESULTS
export TAVILY_SEARCH_DEPTH
export TAVILY_SEARCH_TOPIC
export HF_HOME
export TOKENIZERS_PARALLELISM
export PYTORCH_CUDA_ALLOC_CONF

# Optional: load Tavily key from a private file on Ubelix.
# The file should contain:
#   export TAVILY_API_KEY="tvly-..."
if [[ -f "${HOME}/.hle_search_env" ]]; then
  # shellcheck disable=SC1090
  source "${HOME}/.hle_search_env"
fi

if [[ -z "${TAVILY_API_KEY:-}" ]]; then
  echo "ERROR: TAVILY_API_KEY is not configured."
  echo "Create ~/.hle_search_env or export TAVILY_API_KEY before running."
  exit 1
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

#  if [[ "${SKIP_EXISTING}" == "1" && -s "${output_file}" ]]; then
#    echo "[SKIP] ${model_tag} / ${agent}: ${output_file} already exists."
#    return 0
#  fi

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

write_model_summary() {
  local model_name="$1"
  local model_tag="$2"
  local model_dir="${OUTPUT_ROOT}/${model_tag}"
  local summary_file="${model_dir}/summary.md"

  MODEL_DISPLAY_NAME="${model_name}" \
  MODEL_RESULT_DIR="${model_dir}" \
  MODEL_SUMMARY_FILE="${summary_file}" \
  python - <<'PY'
import csv
import json
import os
from pathlib import Path

model_name = os.environ["MODEL_DISPLAY_NAME"]
result_dir = Path(os.environ["MODEL_RESULT_DIR"])
summary_file = Path(os.environ["MODEL_SUMMARY_FILE"])
agents = [
    "direct",
    "feedback",
    "tool",
#    "tool_search",
    "oracle_feedback",
    "oracle_tool",
]


def load(path: Path):
    rows = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def is_correct(row):
    return row.get("score", {}).get("exact_match") is True

loaded = {
    agent: load(result_dir / f"{agent}_results.jsonl")
    for agent in agents
}

direct_map = {
    row.get("index"): is_correct(row)
    for row in loaded.get("direct", [])
}

lines = [
    f"# Results for `{model_name}`",
    "",
    "| Agent | Accuracy | Correct / Total | Wrong→Right | Right→Wrong | Net vs Direct |",
    "|---|---:|---:|---:|---:|---:|",
]

for agent in agents:
    rows = loaded[agent]
    total = len(rows)
    correct = sum(is_correct(row) for row in rows)
    accuracy = correct / total if total else 0.0

    if agent == "direct" or not direct_map:
        wr = rw = 0
        net_text = "--"
        wr_text = rw_text = "--"
    else:
        wr = 0
        rw = 0
        for row in rows:
            idx = row.get("index")
            if idx not in direct_map:
                continue
            base = direct_map[idx]
            current = is_correct(row)
            wr += int((not base) and current)
            rw += int(base and (not current))
        wr_text = str(wr)
        rw_text = str(rw)
        net_text = f"{wr - rw:+d}"

    lines.append(
        f"| {agent} | {accuracy:.4f} | {correct} / {total} | "
        f"{wr_text} | {rw_text} | {net_text} |"
    )

summary_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Saved model summary to: {summary_file}")
PY
}

write_overall_summary() {
  MODEL_NAMES_JOINED="$(printf '%s|' "${MODELS[@]}")" \
  MODEL_TAGS_JOINED="$(printf '%s|' "${MODEL_TAGS[@]}")" \
  OUTPUT_ROOT_ENV="${OUTPUT_ROOT}" \
  python - <<'PY'
import csv
import json
import os
from pathlib import Path

model_names = [x for x in os.environ["MODEL_NAMES_JOINED"].split("|") if x]
model_tags = [x for x in os.environ["MODEL_TAGS_JOINED"].split("|") if x]
root = Path(os.environ["OUTPUT_ROOT_ENV"])
agents = [
    "direct",
    "feedback",
    "tool",
    "tool_search",
    "oracle_feedback",
    "oracle_tool",
]


def load(path: Path):
    rows = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def is_correct(row):
    return row.get("score", {}).get("exact_match") is True

records = []
for model_name, model_tag in zip(model_names, model_tags):
    model_dir = root / model_tag
    direct_rows = load(model_dir / "direct_results.jsonl")
    direct_map = {row.get("index"): is_correct(row) for row in direct_rows}

    for agent in agents:
        rows = load(model_dir / f"{agent}_results.jsonl")
        total = len(rows)
        correct = sum(is_correct(row) for row in rows)
        accuracy = correct / total if total else 0.0
        wr = rw = 0

        if agent != "direct" and direct_map:
            for row in rows:
                idx = row.get("index")
                if idx not in direct_map:
                    continue
                base = direct_map[idx]
                current = is_correct(row)
                wr += int((not base) and current)
                rw += int(base and (not current))

        records.append({
            "model": model_name,
            "model_tag": model_tag,
            "agent": agent,
            "accuracy": accuracy,
            "correct": correct,
            "total": total,
            "wrong_to_right": "" if agent == "direct" else wr,
            "right_to_wrong": "" if agent == "direct" else rw,
            "net_vs_direct": "" if agent == "direct" else wr - rw,
        })

csv_path = root / "overall_comparison.csv"
with csv_path.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
    writer.writeheader()
    writer.writerows(records)

md_path = root / "overall_comparison.md"
lines = [
    "# Three-Model HLE Agent Comparison",
    "",
    "| Model | Agent | Accuracy | Correct / Total | Wrong→Right | Right→Wrong | Net vs Direct |",
    "|---|---|---:|---:|---:|---:|---:|",
]
for r in records:
    wr = "--" if r["wrong_to_right"] == "" else str(r["wrong_to_right"])
    rw = "--" if r["right_to_wrong"] == "" else str(r["right_to_wrong"])
    net = "--" if r["net_vs_direct"] == "" else f"{r['net_vs_direct']:+d}"
    lines.append(
        f"| {r['model']} | {r['agent']} | {r['accuracy']:.4f} | "
        f"{r['correct']} / {r['total']} | {wr} | {rw} | {net} |"
    )

lines.extend([
    "",
    "## Notes",
    "",
    "- `tool_search` uses Tavily web search after deterministic-tool routing.",
    "- Oracle agents use the gold answer only inside the evaluator and expose only a correctness signal to the model.",
    "- Qwen3.5 thinking should be disabled in `src/llm_qwen.py` via `enable_thinking=False`.",
])
md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

print(f"Saved overall Markdown comparison to: {md_path}")
print(f"Saved overall CSV comparison to: {csv_path}")
PY
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
echo "Skip existing  : ${SKIP_EXISTING}"
echo "4-bit mode     : ${LOAD_IN_4BIT}"
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

  write_model_summary "${model_name}" "${model_tag}"
done

write_overall_summary

echo
echo "============================================================"
echo "All requested experiments finished."
echo "Overall summary: ${OUTPUT_ROOT}/overall_comparison.md"
echo "Overall CSV    : ${OUTPUT_ROOT}/overall_comparison.csv"
echo "============================================================"
