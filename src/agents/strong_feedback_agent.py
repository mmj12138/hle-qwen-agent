# Author: mmj
# DATE: 10.06.2026
from typing import Any, Dict

from src.agents.base import chat
from src.prompts import (
    BASE_SOLVER_INSTRUCTIONS,
    FEEDBACK_SOLVER_PROMPT,
    FEEDBACK_CRITIC_PROMPT,
    FEEDBACK_REVISION_PROMPT,
)


class StrongFeedbackAgent:
    """
    Strong-critic feedback agent.

    Solver and revision use the base model.
    Critic uses a stronger model.

    This is NOT oracle feedback because the critic does not see the gold answer.
    It is an enhanced feedback setting for testing whether critic reliability
    is the bottleneck.
    """

    name = "strong_feedback"

    def __init__(self, max_iterations: int = 2):
        self.max_iterations = max_iterations

    def run(
        self,
        llm,
        question: str,
        answer_type: str = "",
        critic_llm=None,
    ) -> Dict[str, Any]:
        if critic_llm is None:
            raise ValueError("StrongFeedbackAgent requires critic_llm.")

        # Solver: base model
        solver_prompt = FEEDBACK_SOLVER_PROMPT.format(
            question=question,
            base_instructions=BASE_SOLVER_INSTRUCTIONS,
        )
        current_answer = chat(llm, solver_prompt)

        trace = {
            "agent_type": "strong_feedback",
            "note": (
                "Solver/revision use the base model. "
                "Critic uses a stronger model. "
                "Gold answer is not used."
            ),
            "initial_solution": current_answer,
            "iterations": [],
        }

        for step in range(self.max_iterations):
            # Critic: stronger model
            critic_prompt = FEEDBACK_CRITIC_PROMPT.format(
                question=question,
                current_answer=current_answer,
            )
            feedback = chat(critic_llm, critic_prompt)
            status = self._parse_status(feedback)

            iteration_record = {
                "step": step + 1,
                "critic_model": "stronger_critic",
                "critic_prompt": critic_prompt,
                "feedback": feedback,
                "status": status,
            }

            # Conservative gate:
            # only revise when the stronger critic explicitly says incorrect.
            if status in {"correct", "uncertain"}:
                iteration_record["should_stop"] = True
                iteration_record["stop_reason"] = status
                trace["iterations"].append(iteration_record)
                break

            # Revision: base model
            revision_prompt = FEEDBACK_REVISION_PROMPT.format(
                question=question,
                current_answer=current_answer,
                feedback=feedback,
                base_instructions=BASE_SOLVER_INSTRUCTIONS,
            )
            revised_answer = chat(llm, revision_prompt)

            iteration_record["should_stop"] = False
            iteration_record["stop_reason"] = "strong_critic_marked_incorrect"
            iteration_record["revision_prompt"] = revision_prompt
            iteration_record["revised_answer"] = revised_answer

            current_answer = revised_answer
            trace["iterations"].append(iteration_record)

        return {
            "agent": self.name,
            "final_output": current_answer,
            "trace": trace,
        }

    @staticmethod
    def _parse_status(feedback: str) -> str:
        text = feedback.lower()

        if "status: incorrect" in text:
            return "incorrect"
        if "status: correct" in text:
            return "correct"
        if "status: uncertain" in text:
            return "uncertain"

        # If the critic output format is invalid, keep the current answer.
        return "uncertain"
