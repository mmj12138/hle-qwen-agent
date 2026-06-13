import sys
from pathlib import Path
import argparse
import json
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import get_config
from src.dataset_hle import load_hle_dataset, normalize_hle_item, format_question
from src.llm_qwen import QwenLLM
from src.agents import get_agent
from src.agents.tool_search_agent import ToolSearchAgent
from src.evaluator import score_prediction


def write_jsonl(path: str, records: list[dict]):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def compute_accuracy(records: list[dict]) -> dict:
    valid = [r for r in records if r["score"]["exact_match"] is not None]
    correct = sum(1 for r in valid if r["score"]["exact_match"] is True)
    total = len(valid)
    return {
        "correct": correct,
        "total": total,
        "accuracy": correct / total if total else 0.0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--agent",
        choices=[
            "direct",
            "feedback",
            "tool",
            "tool_search",
            "oracle_feedback",
            "oracle_tool",
            "strong_feedback",
        ],
        required=True,
    )
    parser.add_argument("--split", default=None)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--output", default=None)
    parser.add_argument("--text-only", action="store_true")
    parser.add_argument("--max-iterations", type=int, default=2)
    args = parser.parse_args()

    config = get_config()
    split = args.split or config.hle_split
    output_path = args.output or config.output_path

    data = load_hle_dataset(
        split=split,
        limit=args.limit,
        text_only=args.text_only,
    )

    print(f"Loaded {len(data)} samples.")
    print(f"Agent: {args.agent}")
    print(f"Output path: {output_path}")

    llm = QwenLLM(config)

    critic_llm = None
    if args.agent == "strong_feedback":
        print(f"Loading critic model: {config.critic_model_name}")

        critic_config = get_config()
        critic_config.model_name = config.critic_model_name

        critic_llm = QwenLLM(critic_config)

    agent = get_agent(
        args.agent,
        max_iterations=args.max_iterations,
    )

    records = []

    for idx, item in enumerate(tqdm(data, desc=f"Running {args.agent} agent")):
        ex = normalize_hle_item(dict(item))
        question = format_question(ex)

        common_kwargs = {
            "question": question,
            "answer_type": ex["answer_type"],
        }

        if args.agent == "tool_search":
            result = agent.run(
                llm,
                category=ex.get("category", ""),
                **common_kwargs,
            )
        elif args.agent in {"oracle_feedback", "oracle_tool"}:
            result = agent.run(
                llm,
                gold_answer=ex["answer"],
                **common_kwargs,
            )
        else:
            result = agent.run(llm, **common_kwargs)

        score = score_prediction(
            result["final_output"],
            ex["answer"],
            ex["answer_type"],
        )

        records.append(
            {
                "index": idx,
                "agent": args.agent,
                "category": ex.get("category", ""),
                "answer_type": ex["answer_type"],
                "question": question,
                "gold_answer": ex["answer"],
                "final_output": result["final_output"],
                "score": score,
                "trace": result["trace"],
            }
        )

    write_jsonl(output_path, records)
    metrics = compute_accuracy(records)

    print("=" * 80)
    print("Run finished.")
    print(f"Saved results to: {output_path}")
    print(
        f"Accuracy: {metrics['accuracy']:.4f} "
        f"({metrics['correct']}/{metrics['total']})"
    )
    print("=" * 80)


if __name__ == "__main__":
    main()
