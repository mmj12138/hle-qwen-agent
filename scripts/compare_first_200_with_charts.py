#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

# ============================================================
# Fixed analysis configuration
# ============================================================
# The script is expected at:
#   <project_root>/scripts/compare_first_1000.py
#
# Therefore the parent directory of ``scripts`` is the project root.
# This works both locally and on Ubelix without hard-coded paths.
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
RESULT_ROOT = PROJECT_ROOT / "outputs" / "three_model_comparison"
FIRST_N = 1000

MODELS = [
    {
        "name": "Qwen3.5-0.8B",
        "tag": "qwen35_08b",
        "precision": "BF16/FP16",
    },
    # {
    #     "name": "Qwen2.5-7B-Instruct",
    #     "tag": "qwen25_7b",
    #     "precision": "BF16/FP16",
    # },
    {
        "name": "Qwen3.5-9B",
        "tag": "qwen35_9b",
        "precision": "BF16/FP16",
    },
    {
        "name": "Qwen3.5-27B",
        "tag": "qwen35_27b",
        "precision": "NF4 4-bit",
    },
]

AGENTS = [
    "direct",
    "xmaster_feedback",
    "tool_search",
    # "oracle_feedback",
    # "oracle_tool",
    "xmaster_total",

]

EXTRACT_ROOT = RESULT_ROOT / "first_1000_results"
SUMMARY_CSV = RESULT_ROOT / "first_1000_comparison.csv"
SUMMARY_MD = RESULT_ROOT / "first_1000_comparison.md"
CATEGORY_CSV = RESULT_ROOT / "first_1000_category_comparison.csv"
CATEGORY_MD = RESULT_ROOT / "first_1000_category_comparison.md"
ACCURACY_CHART = RESULT_ROOT / "first_1000_accuracy_by_model_agent.png"
TRANSITION_CHART = RESULT_ROOT / "first_1000_answer_transitions.png"
CATEGORY_CHART_DIR = RESULT_ROOT / "first_1000_category_charts"


def read_first_n_by_index(path: Path, first_n: int) -> dict[int, dict[str, Any]]:
    """Read rows whose dataset index is in [0, first_n).

    Rows are keyed by index, so resumed files or duplicate appended rows do not
    distort the result. If an index appears more than once, the last row wins.
    """
    selected: dict[int, dict[str, Any]] = {}

    if not path.exists():
        return selected

    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                print(f"[WARN] Invalid JSON: {path}:{line_number}: {exc}")
                continue

            try:
                index = int(row["index"])
            except (KeyError, TypeError, ValueError):
                print(f"[WARN] Missing/invalid index: {path}:{line_number}")
                continue

            if 0 <= index < first_n:
                selected[index] = row

    return selected


def is_correct(row: dict[str, Any]) -> bool:
    return row.get("score", {}).get("exact_match") is True


def write_extracted_jsonl(
    model_tag: str,
    agent: str,
    rows_by_index: dict[int, dict[str, Any]],
) -> Path:
    output_dir = EXTRACT_ROOT / model_tag
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{agent}_results.jsonl"

    with output_path.open("w", encoding="utf-8") as handle:
        for index in sorted(rows_by_index):
            handle.write(
                json.dumps(rows_by_index[index], ensure_ascii=False) + "\n"
            )

    return output_path


def display_agent(agent: str) -> str:
    return {
        "direct": "Direct",
        "feedback": "Feedback",
        "tool_search": "Tool",
        "xmaster_feedback": "XMaster-Feedback",
        "xmaster_total": "Sim-XMaster",
        "oracle_feedback": "Oracle Feedback",
        # "oracle_tool": "Oracle Tool",
    }.get(agent, agent)



def create_accuracy_chart(comparison_rows: list[dict[str, Any]]) -> None:
    """Grouped bar chart: first-1000 accuracy by model and agent."""
    complete_rows = [
        row
        for row in comparison_rows
        if row["status"] != "N/A"
        and row["total"] != ""
        and int(row["total"]) > 0
    ]

    model_names = [model["name"] for model in MODELS]
    agent_names = [display_agent(agent) for agent in AGENTS]

    accuracy_lookup = {
        (row["model"], row["agent"]): float(row["accuracy"]) * 100
        for row in complete_rows
    }

    x = np.arange(len(model_names))
    available_agent_names = [
        agent
        for agent in agent_names
        if any((model, agent) in accuracy_lookup for model in model_names)
    ]

    if not available_agent_names:
        print("[WARN] No data available for the accuracy chart.")
        return

    width = min(0.8 / len(available_agent_names), 0.16)

    fig, ax = plt.subplots(figsize=(13, 7))

    offsets = (
        np.arange(len(available_agent_names))
        - (len(available_agent_names) - 1) / 2
    ) * width

    for offset, agent in zip(offsets, available_agent_names):
        values = [
            accuracy_lookup.get((model, agent), np.nan)
            for model in model_names
        ]
        bars = ax.bar(
            x + offset,
            values,
            width,
            label=agent,
        )

        for bar, value in zip(bars, values):
            if np.isnan(value):
                continue
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.25,
                f"{value:.1f}%",
                ha="center",
                va="bottom",
                fontsize=8,
                rotation=90,
            )

    ax.set_title(f"HLE Accuracy by Model and Agent — First {FIRST_N} Samples")
    ax.set_xlabel("Model")
    ax.set_ylabel("Accuracy (%)")
    ax.set_xticks(x)
    ax.set_xticklabels(model_names)
    ax.set_ylim(bottom=0)
    ax.grid(axis="y", alpha=0.3)
    ax.legend(
        title="Agent",
        loc="upper left",
        bbox_to_anchor=(1.01, 1),
    )

    fig.tight_layout()
    fig.savefig(ACCURACY_CHART, dpi=220, bbox_inches="tight")
    plt.close(fig)


def create_transition_chart(comparison_rows: list[dict[str, Any]]) -> None:
    """Grouped horizontal bars for W→R and R→W relative to Direct."""
    rows = [
        row
        for row in comparison_rows
        if row["status"] != "N/A"
        and row["agent"] != "Direct"
        and row["wrong_to_right"] != ""
        and row["right_to_wrong"] != ""
    ]

    if not rows:
        print("[WARN] No data available for the transition chart.")
        return

    labels = [
        f"{row['model']} — {row['agent']}"
        for row in rows
    ]
    wrong_to_right = [
        int(row["wrong_to_right"])
        for row in rows
    ]
    right_to_wrong = [
        -int(row["right_to_wrong"])
        for row in rows
    ]

    y = np.arange(len(labels))
    bar_height = 0.38

    fig_height = max(6, 0.45 * len(labels) + 2)
    fig, ax = plt.subplots(figsize=(13, fig_height))

    positive_bars = ax.barh(
        y - bar_height / 2,
        wrong_to_right,
        height=bar_height,
        label="Wrong → Right",
    )
    negative_bars = ax.barh(
        y + bar_height / 2,
        right_to_wrong,
        height=bar_height,
        label="Right → Wrong",
    )

    for bar, value in zip(positive_bars, wrong_to_right):
        ax.text(
            value + 0.15,
            bar.get_y() + bar.get_height() / 2,
            str(value),
            va="center",
            ha="left",
            fontsize=8,
        )

    for bar, signed_value in zip(negative_bars, right_to_wrong):
        value = abs(signed_value)
        ax.text(
            signed_value - 0.15,
            bar.get_y() + bar.get_height() / 2,
            str(value),
            va="center",
            ha="right",
            fontsize=8,
        )

    ax.axvline(0, linewidth=1)
    ax.set_title(
        f"Answer Transitions Relative to Direct — First {FIRST_N} Samples"
    )
    ax.set_xlabel(
        "Number of changed answers "
        "(improvements right, regressions left)"
    )
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.grid(axis="x", alpha=0.3)
    ax.legend(loc="lower right")

    fig.tight_layout()
    fig.savefig(TRANSITION_CHART, dpi=220, bbox_inches="tight")
    plt.close(fig)



def create_category_correct_charts(
    category_rows: list[dict[str, Any]],
) -> list[Path]:
    """Create one grouped bar chart per model.

    X-axis: HLE category
    Series: agents
    Bar height: number of correct answers

    A separate chart is produced for each model to avoid overcrowding.
    """
    CATEGORY_CHART_DIR.mkdir(parents=True, exist_ok=True)
    saved_paths: list[Path] = []

    for model in MODELS:
        model_name = model["name"]
        model_tag = model["tag"]

        rows = [
            row
            for row in category_rows
            if row["model"] == model_name
        ]

        if not rows:
            print(
                f"[WARN] No category data available for {model_name}."
            )
            continue

        categories = sorted(
            {
                str(row["category"])
                for row in rows
            }
        )
        agents = [
            display_agent(agent)
            for agent in AGENTS
            if any(
                row["agent"] == display_agent(agent)
                for row in rows
            )
        ]

        if not categories or not agents:
            continue

        correct_lookup = {
            (
                str(row["category"]),
                str(row["agent"]),
            ): int(row["correct"])
            for row in rows
        }

        x = np.arange(len(categories))
        width = min(0.82 / max(len(agents), 1), 0.20)
        offsets = (
            np.arange(len(agents))
            - (len(agents) - 1) / 2
        ) * width

        fig_width = max(13, 1.6 * len(categories) + 4)
        fig, ax = plt.subplots(figsize=(fig_width, 7.5))

        for offset, agent in zip(offsets, agents):
            values = [
                correct_lookup.get((category, agent), 0)
                for category in categories
            ]
            bars = ax.bar(
                x + offset,
                values,
                width,
                label=agent,
            )

            for bar, value in zip(bars, values):
                if value == 0:
                    continue
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.08,
                    str(value),
                    ha="center",
                    va="bottom",
                    fontsize=7,
                    rotation=90,
                )

        ax.set_title(
            f"Correct Answers by HLE Category and Agent — "
            f"{model_name}, First {FIRST_N} Samples"
        )
        ax.set_xlabel("HLE category")
        ax.set_ylabel("Number of correct answers")
        ax.set_xticks(x)
        ax.set_xticklabels(
            categories,
            rotation=35,
            ha="right",
        )
        ax.set_ylim(bottom=0)
        ax.grid(axis="y", alpha=0.3)
        ax.legend(
            title="Agent",
            loc="upper left",
            bbox_to_anchor=(1.01, 1),
        )

        output_path = (
            CATEGORY_CHART_DIR
            / f"{model_tag}_correct_by_category_agent.png"
        )
        fig.tight_layout()
        fig.savefig(
            output_path,
            dpi=220,
            bbox_inches="tight",
        )
        plt.close(fig)

        saved_paths.append(output_path)

    return saved_paths


def main() -> None:
    RESULT_ROOT.mkdir(parents=True, exist_ok=True)
    EXTRACT_ROOT.mkdir(parents=True, exist_ok=True)
    CATEGORY_CHART_DIR.mkdir(parents=True, exist_ok=True)

    loaded: dict[tuple[str, str], dict[int, dict[str, Any]]] = {}

    # Load and save reproducible first-1000 subsets.
    for model in MODELS:
        model_dir = RESULT_ROOT / model["tag"]

        for agent in AGENTS:
            source_path = model_dir / f"{agent}_results.jsonl"
            rows_by_index = read_first_n_by_index(source_path, FIRST_N)
            loaded[(model["tag"], agent)] = rows_by_index

            if rows_by_index:
                extracted = write_extracted_jsonl(
                    model["tag"],
                    agent,
                    rows_by_index,
                )
                print(
                    f"[OK] {model['tag']}/{agent}: "
                    f"{len(rows_by_index)}/{FIRST_N} rows -> {extracted}"
                )
            else:
                print(f"[N/A] {model['tag']}/{agent}: no result file")

    comparison_rows: list[dict[str, Any]] = []
    category_rows: list[dict[str, Any]] = []

    for model in MODELS:
        tag = model["tag"]
        direct_map = loaded[(tag, "direct")]

        for agent in AGENTS:
            rows_by_index = loaded[(tag, agent)]
            indices = sorted(rows_by_index)
            total = len(indices)

            if total == 0:
                comparison_rows.append(
                    {
                        "model": model["name"],
                        "precision": model["precision"],
                        "agent": display_agent(agent),
                        "correct": "",
                        "total": "",
                        "accuracy": "",
                        "coverage": f"0/{FIRST_N}",
                        "wrong_to_right": "",
                        "right_to_wrong": "",
                        "net_vs_direct": "",
                        "shared_with_direct": "",
                        "missing_indices": FIRST_N,
                        "status": "N/A",
                    }
                )
                continue

            correct = sum(
                is_correct(rows_by_index[index])
                for index in indices
            )
            accuracy = correct / total

            expected = set(range(FIRST_N))
            missing = sorted(expected - set(indices))

            wrong_to_right: int | str = ""
            right_to_wrong: int | str = ""
            net_vs_direct: int | str = ""
            shared_count: int | str = ""

            if agent != "direct" and direct_map:
                shared = sorted(set(indices) & set(direct_map))
                shared_count = len(shared)
                wrong_to_right = sum(
                    (not is_correct(direct_map[index]))
                    and is_correct(rows_by_index[index])
                    for index in shared
                )
                right_to_wrong = sum(
                    is_correct(direct_map[index])
                    and (not is_correct(rows_by_index[index]))
                    for index in shared
                )
                net_vs_direct = wrong_to_right - right_to_wrong

            comparison_rows.append(
                {
                    "model": model["name"],
                    "precision": model["precision"],
                    "agent": display_agent(agent),
                    "correct": correct,
                    "total": total,
                    "accuracy": accuracy,
                    "coverage": f"{total}/{FIRST_N}",
                    "wrong_to_right": wrong_to_right,
                    "right_to_wrong": right_to_wrong,
                    "net_vs_direct": net_vs_direct,
                    "shared_with_direct": shared_count,
                    "missing_indices": len(missing),
                    "status": "Complete" if total == FIRST_N else "Partial",
                }
            )

            grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for index in indices:
                row = rows_by_index[index]
                category = str(row.get("category") or "Unknown")
                grouped[category].append(row)

            for category, category_data in sorted(grouped.items()):
                category_correct = sum(is_correct(row) for row in category_data)
                category_total = len(category_data)
                category_rows.append(
                    {
                        "model": model["name"],
                        "precision": model["precision"],
                        "agent": display_agent(agent),
                        "category": category,
                        "correct": category_correct,
                        "total": category_total,
                        "accuracy": category_correct / category_total,
                    }
                )

    comparison_fields = [
        "model",
        "precision",
        "agent",
        "correct",
        "total",
        "accuracy",
        "coverage",
        "wrong_to_right",
        "right_to_wrong",
        "net_vs_direct",
        "shared_with_direct",
        "missing_indices",
        "status",
    ]

    with SUMMARY_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=comparison_fields)
        writer.writeheader()
        writer.writerows(comparison_rows)

    md_lines = [
        f"# HLE First-{FIRST_N} Comparison",
        "",
        f"All results are restricted to dataset indices `0–{FIRST_N - 1}`.",
        "",
        "| Model | Precision | Agent | Accuracy | Correct / N | Coverage | W→R | R→W | Net vs Direct | Status |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]

    for row in comparison_rows:
        if row["status"] == "N/A":
            md_lines.append(
                f"| {row['model']} | {row['precision']} | {row['agent']} | "
                f"N/A | N/A | 0/{FIRST_N} | N/A | N/A | N/A | N/A |"
            )
            continue

        wr = (
            "—"
            if row["wrong_to_right"] == ""
            else str(row["wrong_to_right"])
        )
        rw = (
            "—"
            if row["right_to_wrong"] == ""
            else str(row["right_to_wrong"])
        )
        net = (
            "—"
            if row["net_vs_direct"] == ""
            else f"{int(row['net_vs_direct']):+d}"
        )

        md_lines.append(
            f"| {row['model']} | {row['precision']} | {row['agent']} | "
            f"{float(row['accuracy']):.2%} | "
            f"{row['correct']} / {row['total']} | "
            f"{row['coverage']} | {wr} | {rw} | {net} | "
            f"{row['status']} |"
        )

    md_lines.extend(
        [
            "",
            "## Interpretation notes",
            "",
            "- Only identical indices `0–99` are compared.",
            "- `W→R` and `R→W` are computed against Direct on shared indices.",
            "- A partial result is retained but marked as `Partial`.",
            "- Qwen3.5-9B is configured as BF16/FP16; update the precision label if your run used quantization.",
            "- Qwen3.5-27B uses NF4 4-bit quantization.",
            # "- `Tool + Search` may be available only for Qwen2.5-7B-Instruct; missing combinations are shown as `N/A`.",
            "",
            f"Extracted subsets: `{EXTRACT_ROOT}`",
        ]
    )

    SUMMARY_MD.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    category_fields = [
        "model",
        "precision",
        "agent",
        "category",
        "correct",
        "total",
        "accuracy",
    ]
    with CATEGORY_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=category_fields)
        writer.writeheader()
        writer.writerows(category_rows)

    category_md_lines = [
        f"# HLE First-{FIRST_N} Category Comparison",
        "",
        "| Model | Agent | Category | Accuracy | Correct / N |",
        "|---|---|---|---:|---:|",
    ]
    for row in category_rows:
        category_md_lines.append(
            f"| {row['model']} | {row['agent']} | {row['category']} | "
            f"{float(row['accuracy']):.2%} | "
            f"{row['correct']} / {row['total']} |"
        )

    CATEGORY_MD.write_text(
        "\n".join(category_md_lines) + "\n",
        encoding="utf-8",
    )

    create_accuracy_chart(comparison_rows)
    create_transition_chart(comparison_rows)
    category_chart_paths = create_category_correct_charts(category_rows)

    print()
    print(f"Saved main table:     {SUMMARY_MD}")
    print(f"Saved main CSV:       {SUMMARY_CSV}")
    print(f"Saved category table: {CATEGORY_MD}")
    print(f"Saved category CSV:   {CATEGORY_CSV}")
    print(f"Saved accuracy chart: {ACCURACY_CHART}")
    print(f"Saved transition chart: {TRANSITION_CHART}")
    for chart_path in category_chart_paths:
        print(f"Saved category chart:   {chart_path}")


if __name__ == "__main__":
    main()
