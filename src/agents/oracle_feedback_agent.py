# Author: mmj
# DATE: 01.06.2026

from typing import Any, Dict

from src.agents.base import chat
from src.evaluator import score_prediction
from src.prompts import (
    BASE_SOLVER_INSTRUCTIONS,
    FEEDBACK_SOLVER_PROMPT,
    ORACLE_REVISION_PROMPT,
)


class OracleFeedbackAgent:
    """
    Oracle / evaluator-gated feedback agent.

    This agent uses the gold answer only to check whether the current prediction
    is already correct. It does NOT reveal the gold answer to the model.

    This is not a deployable setting. It is an upper-bound diagnostic experiment.
    """

    name = "oracle_feedback"

    def __init__(self, max_iterations: int = 2):
        self.max_iterations = max_iterations

    def run(
        self,
        llm,
        question: str,
        answer_type: str = "",
        gold_answer: str | None = None,
    ) -> Dict[str, Any]:
        if gold_answer is None:
            raise ValueError("OracleFeedbackAgent requires gold_answer.")

        solver_prompt = FEEDBACK_SOLVER_PROMPT.format(
            question=question,
            base_instructions=BASE_SOLVER_INSTRUCTIONS,
        )
        current_answer = chat(llm, solver_prompt)

        trace = {
            "agent_type": "oracle_feedback",
            "note": (
                "Uses gold answer only for evaluator-based correctness checking. "
                "Gold answer is not shown to the model."
            ),
            "initial_solution": current_answer,
            "iterations": [],
        }

        for step in range(self.max_iterations + 1):
            score = score_prediction(
                prediction_text=current_answer,
                gold_answer=gold_answer,
                answer_type=answer_type,
            )

            iteration_record = {
                "step": step + 1,
                "current_answer": current_answer,
                "oracle_score": score,
                "oracle_exact_match": score.get("exact_match", False),
            }

            if score.get("exact_match", False):
                iteration_record["should_stop"] = True
                iteration_record["stop_reason"] = "oracle_exact_match"
                trace["iterations"].append(iteration_record)
                break

            if step >= self.max_iterations:
                iteration_record["should_stop"] = True
                iteration_record["stop_reason"] = "max_iterations_reached"
                trace["iterations"].append(iteration_record)
                break

            revision_prompt = ORACLE_REVISION_PROMPT.format(
                question=question,
                current_answer=current_answer,
                answer_type=answer_type,
                base_instructions=BASE_SOLVER_INSTRUCTIONS,
            )

            revised_answer = chat(llm, revision_prompt)

            iteration_record["should_stop"] = False
            iteration_record["stop_reason"] = "oracle_marked_incorrect"
            iteration_record["revision_prompt"] = revision_prompt
            iteration_record["revised_answer"] = revised_answer
            trace["iterations"].append(iteration_record)

            current_answer = revised_answer

        return {
            "agent": self.name,
            "final_output": current_answer,
            "trace": trace,
        }
