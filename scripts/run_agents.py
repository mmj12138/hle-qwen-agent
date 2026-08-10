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


def compute_generation_summary(records: list[dict]) -> dict:
    calls = [
        call
        for record in records
        for call in record.get("generation_diagnostics", [])
    ]

    total_calls = len(calls)
    reached_limit_calls = sum(
        1 for call in calls if call.get("reached_token_limit") is True
    )
    empty_output_calls = sum(
        1 for call in calls if call.get("output_empty") is True
    )

    generated_counts = [
        int(call["generated_tokens"])
        for call in calls
        if call.get("generated_tokens") is not None
    ]

    return {
        "total_model_calls": total_calls,
        "reached_token_limit_calls": reached_limit_calls,
        "reached_token_limit_rate": (
            reached_limit_calls / total_calls if total_calls else 0.0
        ),
        "empty_output_calls": empty_output_calls,
        "average_generated_tokens": (
            sum(generated_counts) / len(generated_counts)
            if generated_counts
            else 0.0
        ),
        "max_generated_tokens": max(generated_counts) if generated_counts else 0,
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
            "xmaster_feedback",
            "xmaster_total",
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

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    completed_indices = set()
    records = []

    if output_file.exists():
        with output_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                record = json.loads(line)
                records.append(record)
                completed_indices.add(record["index"])

    print(f"Resuming with {len(completed_indices)} completed samples.")

    with output_file.open("a", encoding="utf-8", buffering=1) as f:
        for idx, item in enumerate(
            tqdm(data, desc=f"Running {args.agent} agent")
        ):
            if idx in completed_indices:
                continue

            ex = normalize_hle_item(dict(item))
            question = format_question(ex)

            # Store diagnostics only for calls made for this sample.
            llm.reset_generation_diagnostics()
            if critic_llm is not None:
                critic_llm.reset_generation_diagnostics()

            if args.agent == "oracle_feedback":
                result = agent.run(
                    llm,
                    question=question,
                    answer_type=ex["answer_type"],
                    gold_answer=ex["answer"],
                )

            elif args.agent == "oracle_tool":
                result = agent.run(
                    llm,
                    question=question,
                    answer_type=ex["answer_type"],
                    gold_answer=ex["answer"],
                )

            elif args.agent == "tool_search":
                result = agent.run(
                    llm,
                    question=question,
                    answer_type=ex["answer_type"],
                    category=ex["category"],
                )
            elif args.agent == "xmaster_total":
                result = agent.run(
                    llm,
                    question=question,
                    answer_type=ex["answer_type"],
                    category=ex["category"],
                )
            else:
                result = agent.run(
                    llm,
                    question=question,
                    answer_type=ex["answer_type"],
                )

            generation_diagnostics = llm.get_generation_diagnostics(clear=True)
            if critic_llm is not None:
                critic_diagnostics = critic_llm.get_generation_diagnostics(
                    clear=True
                )
            else:
                critic_diagnostics = []

            score = score_prediction(
                result["final_output"],
                ex["answer"],
                ex["answer_type"],
            )

            record = {
                "index": idx,
                "agent": args.agent,
                "category": ex["category"],
                "answer_type": ex["answer_type"],
                "question": question,
                "gold_answer": ex["answer"],
                "final_output": result["final_output"],
                "score": score,
                "trace": result["trace"],
                "generation_diagnostics": generation_diagnostics,
            }

            if critic_diagnostics:
                record["critic_generation_diagnostics"] = critic_diagnostics

            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            f.flush()

            records.append(record)

    metrics = compute_accuracy(records)
    generation_summary = compute_generation_summary(records)

    print("=" * 80)
    print("Run finished.")
    print(f"Saved results to: {output_path}")
    print(
        f"Accuracy: {metrics['accuracy']:.4f} "
        f"({metrics['correct']}/{metrics['total']})"
    )
    print(
        "Generation diagnostics: "
        f"limit reached in "
        f"{generation_summary['reached_token_limit_calls']}/"
        f"{generation_summary['total_model_calls']} calls "
        f"({generation_summary['reached_token_limit_rate']:.2%}); "
        f"average generated tokens="
        f"{generation_summary['average_generated_tokens']:.1f}"
    )
    print("=" * 80)


if __name__ == "__main__":
    main()
