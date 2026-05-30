from __future__ import annotations

from typing import Any, Dict, Optional
from datasets import load_dataset

from src.data_utils import is_text_only

def load_hle_dataset(
    split: str = "test",
    limit: Optional[int] = None,
    text_only: bool = False,
):
    """
    Load HLE from Hugging Face.

    If text_only=True:
    - load the full split first
    - filter out samples with images
    - then apply limit
    """
    ds = load_dataset("cais/hle", token=True)

    if split not in ds:
        available = list(ds.keys())
        raise ValueError(f"Split '{split}' not found. Available splits: {available}")

    data = ds[split]

    if text_only:
        data = data.filter(is_text_only)

    if limit is not None:
        data = data.select(range(min(limit, len(data))))

    return data


def normalize_hle_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    HLE field names may be adjusted by dataset maintainers.
    This function tries to normalize common fields.

    Run scripts/check_dataset.py first to inspect the real fields.
    """
    question = (
        item.get("question")
        or item.get("Question")
        or item.get("prompt")
        or item.get("problem")
        or ""
    )

    answer = (
        item.get("answer")
        or item.get("Answer")
        or item.get("gold_answer")
        or item.get("correct_answer")
        or ""
    )

    choices = (
        item.get("choices")
        or item.get("options")
        or item.get("multiple_choice_options")
        or None
    )

    category = (
        item.get("category")
        or item.get("subject")
        or item.get("field")
        or item.get("domain")
        or "unknown"
    )

    answer_type = (
        item.get("answer_type")
        or item.get("question_type")
        or ("multiple_choice" if choices else "short_answer")
    )

    return {
        "question": question,
        "answer": answer,
        "choices": choices,
        "category": category,
        "answer_type": answer_type,
        "raw": item,
    }


def format_question(example: Dict[str, Any]) -> str:
    question = example["question"]
    choices = example.get("choices")

    if choices:
        if isinstance(choices, dict):
            choice_text = "\n".join([f"{k}. {v}" for k, v in choices.items()])
        elif isinstance(choices, list):
            labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            choice_text = "\n".join([f"{labels[i]}. {c}" for i, c in enumerate(choices)])
        else:
            choice_text = str(choices)

        return f"{question}\n\nChoices:\n{choice_text}"

    return question
