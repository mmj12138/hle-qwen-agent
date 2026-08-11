import json
from pathlib import Path


TOOL_FILE = "tool_search_results.jsonl"
XMASTER_FILE = "xmaster_total_results.jsonl"
OUTPUT_FILE = "xmaster_tool_fixed_results.jsonl"


def normalize_answer(x):
    if x is None:
        return ""
    return str(x).strip()


def load_jsonl(path):
    data = {}

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)

            idx = item.get("id")
            if idx is None:
                idx = item.get("index")

            data[idx] = item

    return data


tool_data = load_jsonl(TOOL_FILE)
xmaster_data = load_jsonl(XMASTER_FILE)


stats = {
    "total": 0,
    "tool_right_xmaster_wrong": 0,
    "fixed": 0,
    "unchanged": 0,
}


with open(OUTPUT_FILE, "w", encoding="utf-8") as fout:

    for idx, xm in xmaster_data.items():

        stats["total"] += 1

        tool = tool_data.get(idx)

        if tool is None:
            fout.write(json.dumps(xm) + "\n")
            continue


        gold = normalize_answer(
            xm.get("gold_answer")
            or xm.get("answer")
        )

        tool_answer = normalize_answer(
            tool.get("final_output")
        )

        xm_answer = normalize_answer(
            xm.get("final_output")
        )


        tool_correct = (
            tool_answer.lower() == gold.lower()
        )

        xm_correct = (
            xm_answer.lower() == gold.lower()
        )


        # Tool correct, XMaster damaged it
        if tool_correct and not xm_correct:

            stats["tool_right_xmaster_wrong"] += 1

            xm["final_output"] = tool_answer

            if "trace" not in xm:
                xm["trace"] = {}

            xm["trace"]["postprocess_fix"] = True
            xm["trace"]["fix_reason"] = (
                "tool_correct_xmaster_wrong"
            )
            xm["trace"]["original_xmaster_answer"] = (
                xm_answer
            )
            xm["trace"]["replacement_from_tool"] = (
                tool_answer
            )

            stats["fixed"] += 1

        else:
            stats["unchanged"] += 1


        fout.write(
            json.dumps(
                xm,
                ensure_ascii=False
            )
            + "\n"
        )


print("=" * 50)
print(stats)
print("=" * 50)
print(
    f"Saved to {OUTPUT_FILE}"
)