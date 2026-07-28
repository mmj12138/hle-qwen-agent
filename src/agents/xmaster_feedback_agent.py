# Author: mmj
# Lightweight X-Master-inspired multi-candidate feedback agent
from __future__ import annotations

from typing import Any, Dict, List

from src.prompts import (
    BASE_SOLVER_INSTRUCTIONS,
    XMASTER_FEEDBACK_CANDIDATE_PROMPT,
    XMASTER_FEEDBACK_COMPARE_PROMPT,
    XMASTER_FEEDBACK_SELECT_PROMPT,
)
from src.agents.base import chat


class XMasterFeedbackAgent:
    """
    Generate N independent candidates, compare them, and select/revise
    a final answer. The existing FeedbackAgent remains unchanged.
    """

    name = "xmaster_feedback"

    def __init__(self, num_candidates: int = 2):
        if num_candidates < 2:
            raise ValueError(
                "XMasterFeedbackAgent requires at least 2 candidates."
            )
        self.num_candidates = int(num_candidates)

    def run(
        self,
        llm,
        question: str,
        answer_type: str = "",
    ) -> Dict[str, Any]:
        candidates: List[str] = []

        for candidate_index in range(1, self.num_candidates + 1):
            prompt = XMASTER_FEEDBACK_CANDIDATE_PROMPT.format(
                question=question,
                answer_type=answer_type or "unspecified",
                candidate_index=candidate_index,
                base_instructions=BASE_SOLVER_INSTRUCTIONS,
            )
            candidates.append(chat(llm, prompt))

        formatted_candidates = self._format_candidates(candidates)

        compare_prompt = XMASTER_FEEDBACK_COMPARE_PROMPT.format(
            question=question,
            answer_type=answer_type or "unspecified",
            candidates=formatted_candidates,
        )
        comparison = chat(llm, compare_prompt)

        select_prompt = XMASTER_FEEDBACK_SELECT_PROMPT.format(
            question=question,
            answer_type=answer_type or "unspecified",
            candidates=formatted_candidates,
            comparison=comparison,
        )
        final_output = chat(llm, select_prompt)

        return {
            "agent": self.name,
            "final_output": final_output,
            "trace": {
                "num_candidates": self.num_candidates,
                "candidates": [
                    {
                        "candidate_index": index,
                        "output": output,
                    }
                    for index, output in enumerate(candidates, start=1)
                ],
                "comparison": comparison,
                "final_selection": final_output,
            },
        }

    @staticmethod
    def _format_candidates(candidates: List[str]) -> str:
        return "\n\n".join(
            f"Candidate {index}:\n{candidate.strip()}"
            for index, candidate in enumerate(candidates, start=1)
        )
