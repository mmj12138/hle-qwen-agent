# Author: mmj
# DATE: 30.05.2026
from typing import Any, Dict

from src.prompts import (
    BASE_SOLVER_INSTRUCTIONS,
    FEEDBACK_SOLVER_PROMPT,
    FEEDBACK_CRITIC_PROMPT,
    FEEDBACK_REVISION_PROMPT,
)
from src.agents.base import chat


class FeedbackAgent:
    name = "feedback"

    def __init__(self, max_iterations: int = 2):
        self.max_iterations = max_iterations

    def run(self, llm, question: str, answer_type: str = "") -> Dict[str, Any]:
        solver_prompt = FEEDBACK_SOLVER_PROMPT.format(
            question=question,
            base_instructions=BASE_SOLVER_INSTRUCTIONS,
        )
        current_answer = chat(llm, solver_prompt)

        trace = {
            "initial_solution": current_answer,
            "iterations": [],
        }

        for step in range(self.max_iterations):
            critic_prompt = FEEDBACK_CRITIC_PROMPT.format(
                question=question,
                current_answer=current_answer,
            )
            feedback = chat(llm, critic_prompt)

            should_stop = self._should_stop(feedback)

            iteration_record = {
                "step": step + 1,
                "critic_prompt": critic_prompt,
                "feedback": feedback,
                "should_stop": should_stop,
            }

            if should_stop:
                trace["iterations"].append(iteration_record)
                break

            revision_prompt = FEEDBACK_REVISION_PROMPT.format(
                question=question,
                current_answer=current_answer,
                feedback=feedback,
                base_instructions=BASE_SOLVER_INSTRUCTIONS,
            )
            current_answer = chat(llm, revision_prompt)

            iteration_record["revision_prompt"] = revision_prompt
            iteration_record["revised_answer"] = current_answer
            trace["iterations"].append(iteration_record)

        return {
            "agent": self.name,
            "final_output": current_answer,
            "trace": trace,
        }

    @staticmethod
    def _should_stop(feedback: str) -> bool:
        return "status: correct" in feedback.lower()