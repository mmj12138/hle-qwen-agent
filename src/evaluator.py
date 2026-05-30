from __future__ import annotations

import re
import string
from typing import Any, Dict


def extract_final_answer(text: str) -> str:
    """
    Extract text after 'Final Answer:' or 'Initial Answer:'.
    Falls back to the last non-empty line.
    """
    patterns = [
        r"Final Answer\s*:\s*(.+)",
        r"Initial Answer\s*:\s*(.+)",
        r"Answer\s*:\s*(.+)",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        if matches:
            return matches[-1].strip()

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[-1] if lines else ""


def normalize_multiple_choice(ans: Any) -> str:
    if ans is None:
        return ""

    ans = str(ans).strip().upper()

    # Examples:
    # "D"
    # "D."
    # "(D)"
    # "Option D"
    # "Final Answer: D"
    m = re.search(r"\b([A-Z])\b", ans)
    return m.group(1) if m else ans


def normalize_exact_match(ans: Any) -> str:
    if ans is None:
        return ""

    ans = str(ans).strip()

    # Remove trailing punctuation that models often add.
    ans = ans.strip()
    ans = ans.rstrip(".")

    # Normalize spaces but keep mathematical symbols like +, -, Z, etc.
    ans = re.sub(r"\s+", " ", ans)

    return ans.lower()


def normalize_answer(ans: Any, answer_type: str = "") -> str:
    answer_type = (answer_type or "").lower()

    if "multiple" in answer_type or "choice" in answer_type:
        return normalize_multiple_choice(ans)

    return normalize_exact_match(ans)


def score_prediction(
    prediction_text: str,
    gold_answer: Any,
    answer_type: str = "",
) -> Dict[str, Any]:
    pred = extract_final_answer(prediction_text)

    norm_pred = normalize_answer(pred, answer_type)
    norm_gold = normalize_answer(gold_answer, answer_type)

    exact = norm_pred == norm_gold if norm_gold else None

    return {
        "prediction": pred,
        "gold": gold_answer,
        "normalized_prediction": norm_pred,
        "normalized_gold": norm_gold,
        "exact_match": exact,
    }