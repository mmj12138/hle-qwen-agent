import argparse
import json
from collections import defaultdict
from pathlib import Path


def load_jsonl(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def accuracy(rows):
    valid = [
        r for r in rows
        if r.get("score", {}).get("exact_match") is not None
    ]

    correct = sum(
        1 for r in valid
        if r["score"]["exact_match"] is True
    )

    total = len(valid)
    acc = correct / total if total else 0.0

    return correct, total, acc


def summarize_file(path):
    rows = load_jsonl(path)

    if not rows:
        return {
            "file": path,
            "agent": "unknown",
            "rows": [],
            "correct": 0,
            "total": 0,
            "accuracy": 0.0,
        }

    agent = rows[0].get("agent", Path(path).stem)
    correct, total, acc = accuracy(rows)

    return {
        "file": path,
        "agent": agent,
        "rows": rows,
        "correct": correct,
        "total": total,
        "accuracy": acc,
    }


def summarize_by_category(all_rows):
    groups = defaultdict(list)

    for r in all_rows:
        agent = r.get("agent", "unknown")
        category = r.get("category", "unknown")
        groups[(agent, category)].append(r)

    results = []

    for (agent, category), rows in sorted(groups.items()):
        correct, total, acc = accuracy(rows)

        results.append(
            {
                "agent": agent,
                "category": category,
                "correct": correct,
                "total": total,
                "accuracy": acc,
            }
        )

    return results


def build_index(rows):
    """
    Build a comparable index by question index.
    This assumes all agents were run on the same filtered dataset
    with the same limit.
    """
    return {
        r["index"]: r
        for r in rows
    }


def compare_against_direct(direct_rows, other_rows, other_name):
    direct_map = build_index(direct_rows)
    other_map = build_index(other_rows)

    shared_indices = sorted(set(direct_map.keys()) & set(other_map.keys()))

    wrong_to_right = []
    right_to_wrong = []
    same_correct = []
    same_wrong = []

    for idx in shared_indices:
        d = direct_map[idx]
        o = other_map[idx]

        d_correct = d.get("score", {}).get("exact_match")
        o_correct = o.get("score", {}).get("exact_match")

        if d_correct is False and o_correct is True:
            wrong_to_right.append((idx, d, o))
        elif d_correct is True and o_correct is False:
            right_to_wrong.append((idx, d, o))
        elif d_correct is True and o_correct is True:
            same_correct.append((idx, d, o))
        elif d_correct is False and o_correct is False:
            same_wrong.append((idx, d, o))

    return {
        "agent": other_name,
        "shared_total": len(shared_indices),
        "wrong_to_right": wrong_to_right,
        "right_to_wrong": right_to_wrong,
        "same_correct": same_correct,
        "same_wrong": same_wrong,
    }


def short_answer(row):
    score = row.get("score", {})
    pred = score.get("prediction", "")
    gold = score.get("gold", row.get("gold_answer", ""))
    return pred, gold


def question_preview(row, max_len=120):
    q = row.get("question", "").replace("\n", " ")
    if len(q) > max_len:
        q = q[:max_len] + "..."
    return q


def make_markdown_report(file_summaries, category_summary, comparisons):
    lines = []

    lines.append("# HLE Agent Experiment Summary")
    lines.append("")

    lines.append("## Overall Accuracy")
    lines.append("")
    lines.append("| Agent | Accuracy | Correct / Total | File |")
    lines.append("|---|---:|---:|---|")

    for s in file_summaries:
        lines.append(
            f"| {s['agent']} | {s['accuracy']:.4f} | "
            f"{s['correct']} / {s['total']} | `{s['file']}` |"
        )

    lines.append("")
    lines.append("## Accuracy by Category")
    lines.append("")
    lines.append("| Agent | Category | Accuracy | Correct / Total |")
    lines.append("|---|---|---:|---:|")

    for row in category_summary:
        lines.append(
            f"| {row['agent']} | {row['category']} | "
            f"{row['accuracy']:.4f} | {row['correct']} / {row['total']} |"
        )

    if comparisons:
        lines.append("")
        lines.append("## Comparison Against Direct Agent")
        lines.append("")

        for comp in comparisons:
            agent = comp["agent"]
            total = comp["shared_total"]

            w2r = len(comp["wrong_to_right"])
            r2w = len(comp["right_to_wrong"])
            sc = len(comp["same_correct"])
            sw = len(comp["same_wrong"])

            lines.append(f"### Direct vs {agent}")
            lines.append("")
            lines.append(f"Shared examples: **{total}**")
            lines.append("")
            lines.append("| Case type | Count |")
            lines.append("|---|---:|")
            lines.append(f"| Wrong → Right | {w2r} |")
            lines.append(f"| Right → Wrong | {r2w} |")
            lines.append(f"| Same Correct | {sc} |")
            lines.append(f"| Same Wrong | {sw} |")
            lines.append("")

            if comp["wrong_to_right"]:
                lines.append("#### Examples: Wrong → Right")
                lines.append("")
                lines.append("| Index | Category | Question | Direct Pred | Agent Pred | Gold |")
                lines.append("|---:|---|---|---|---|---|")

                for idx, d, o in comp["wrong_to_right"][:5]:
                    d_pred, gold = short_answer(d)
                    o_pred, _ = short_answer(o)
                    lines.append(
                        f"| {idx} | {d.get('category', '')} | "
                        f"{question_preview(d)} | `{d_pred}` | `{o_pred}` | `{gold}` |"
                    )
                lines.append("")

            if comp["right_to_wrong"]:
                lines.append("#### Examples: Right → Wrong")
                lines.append("")
                lines.append("| Index | Category | Question | Direct Pred | Agent Pred | Gold |")
                lines.append("|---:|---|---|---|---|---|")

                for idx, d, o in comp["right_to_wrong"][:5]:
                    d_pred, gold = short_answer(d)
                    o_pred, _ = short_answer(o)
                    lines.append(
                        f"| {idx} | {d.get('category', '')} | "
                        f"{question_preview(d)} | `{d_pred}` | `{o_pred}` | `{gold}` |"
                    )
                lines.append("")

    return "\n".join(lines) + "\n"


def print_overall(file_summaries):
    print("=" * 80)
    print("Overall accuracy")
    print("=" * 80)

    for s in file_summaries:
        print(
            f"{s['agent']:10s} | "
            f"accuracy = {s['accuracy']:.4f} "
            f"({s['correct']}/{s['total']}) | "
            f"{s['file']}"
        )


def print_category(category_summary):
    print()
    print("=" * 80)
    print("Accuracy by category")
    print("=" * 80)

    for row in category_summary:
        print(
            f"{row['agent']:10s} | "
            f"{row['category'][:30]:30s} | "
            f"{row['accuracy']:.4f} "
            f"({row['correct']}/{row['total']})"
        )


def print_comparisons(comparisons):
    if not comparisons:
        return

    print()
    print("=" * 80)
    print("Comparison against Direct Agent")
    print("=" * 80)

    for comp in comparisons:
        print(f"Direct vs {comp['agent']}")
        print(f"  shared examples : {comp['shared_total']}")
        print(f"  wrong -> right  : {len(comp['wrong_to_right'])}")
        print(f"  right -> wrong  : {len(comp['right_to_wrong'])}")
        print(f"  same correct    : {len(comp['same_correct'])}")
        print(f"  same wrong      : {len(comp['same_wrong'])}")
        print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        nargs="+",
        required=True,
        help="One or more result jsonl files.",
    )
    parser.add_argument(
        "--output",
        default="outputs/summary.md",
        help="Path to save the markdown summary report.",
    )
    args = parser.parse_args()

    file_summaries = [
        summarize_file(path)
        for path in args.input
    ]

    all_rows = []
    for s in file_summaries:
        all_rows.extend(s["rows"])

    category_summary = summarize_by_category(all_rows)

    # Compare feedback/tool against direct if direct exists.
    direct_summary = None
    for s in file_summaries:
        if s["agent"] == "direct":
            direct_summary = s
            break

    comparisons = []
    if direct_summary is not None:
        for s in file_summaries:
            if s["agent"] != "direct":
                comparisons.append(
                    compare_against_direct(
                        direct_summary["rows"],
                        s["rows"],
                        s["agent"],
                    )
                )

    print_overall(file_summaries)
    print_category(category_summary)
    print_comparisons(comparisons)

    report = make_markdown_report(
        file_summaries=file_summaries,
        category_summary=category_summary,
        comparisons=comparisons,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")

    print("=" * 80)
    print(f"Summary report saved to: {output_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()