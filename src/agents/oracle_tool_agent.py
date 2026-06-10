# Author: mmj
# DATE: 10.06.2026
from typing import Any, Dict

from src.agents.base import chat
from src.agents.tool_agent import ToolAgent
from src.evaluator import score_prediction
from src.prompts import BASE_SOLVER_INSTRUCTIONS, ORACLE_REVISION_PROMPT


class OracleToolAgent:
    """
    Oracle Tool Agent.

    This wraps the benchmark evaluator as a correctness-checking tool.
    The evaluator uses the gold answer internally to return correct/incorrect,
    but the gold answer is NOT shown to the model.

    This is not a deployable setting. It is an upper-bound diagnostic experiment.
    """

    name = "oracle_tool"

    def __init__(self, max_iterations: int = 2):
        self.max_iterations = max_iterations
        self.base_tool_agent = ToolAgent(max_iterations=max_iterations)

    def run(
        self,
        llm,
        question: str,
        answer_type: str = "",
        gold_answer: str | None = None,
    ) -> Dict[str, Any]:
        if gold_answer is None:
            raise ValueError("OracleToolAgent requires gold_answer.")

        # Step 1: get initial answer from normal Tool Agent
        initial_result = self.base_tool_agent.run(
            llm,
            question=question,
            answer_type=answer_type,
        )

        current_answer = initial_result["final_output"]

        trace = {
            "agent_type": "oracle_tool",
            "note": (
                "Uses the benchmark evaluator as a correctness-checking tool. "
                "Gold answer is used only inside the evaluator and is not shown to the model."
            ),
            "initial_tool_result": initial_result,
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
                "oracle_tool_score": score,
                "oracle_exact_match": score.get("exact_match", False),
            }

            if score.get("exact_match", False):
                iteration_record["should_stop"] = True
                iteration_record["stop_reason"] = "oracle_tool_exact_match"
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
            iteration_record["stop_reason"] = "oracle_tool_marked_incorrect"
            iteration_record["revision_prompt"] = revision_prompt
            iteration_record["revised_answer"] = revised_answer
            trace["iterations"].append(iteration_record)

            current_answer = revised_answer

        return {
            "agent": self.name,
            "final_output": current_answer,
            "trace": trace,
        }