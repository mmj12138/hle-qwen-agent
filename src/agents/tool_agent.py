# Author: mmj
# DATE: 30.05.2026
import json
from typing import Any, Dict

from src.prompts import (
    BASE_SOLVER_INSTRUCTIONS,
    TOOL_PLANNER_PROMPT,
    TOOL_SOLVER_PROMPT,
    TOOL_VERIFIER_PROMPT,
)
from src.tools import run_tools, rule_based_tool_plan
from src.agents.base import chat


class ToolAgent:
    name = "tool"

    def __init__(self, max_iterations: int = 2):
        self.max_iterations = max_iterations

    def run(self, llm, question: str, answer_type: str = "") -> Dict[str, Any]:
        trace = {
            "iterations": [],
        }

        verifier_feedback = "None."
        final_answer = ""

        for step in range(self.max_iterations):
            planner_question = question
            if verifier_feedback != "None.":
                planner_question += "\n\nPrevious verifier feedback:\n" + verifier_feedback

            # Use deterministic rule-based planning to avoid noisy tool selection.
            plan = rule_based_tool_plan(question, answer_type=answer_type)
            raw_plan = json.dumps(plan, ensure_ascii=False)

            tool_results = run_tools(plan, question, answer_type=answer_type)
            planner_prompt = "Rule-based planner was used."

            solver_prompt = TOOL_SOLVER_PROMPT.format(
                question=question,
                tool_results=json.dumps(tool_results, ensure_ascii=False, indent=2),
                verifier_feedback=verifier_feedback,
                base_instructions=BASE_SOLVER_INSTRUCTIONS,
            )
            candidate_answer = chat(llm, solver_prompt)

            verifier_prompt = TOOL_VERIFIER_PROMPT.format(
                question=question,
                candidate_answer=candidate_answer,
                tool_results=json.dumps(tool_results, ensure_ascii=False, indent=2),
            )
            verifier_output = chat(llm, verifier_prompt)

            should_stop = self._should_stop(verifier_output)

            if should_stop:
                # Verifier says the candidate answer is correct.
                # Keep the solver's candidate answer instead of replacing it with verifier output.
                final_answer = candidate_answer
            else:
                # Verifier says incorrect.
                # Use verifier output as feedback for the next iteration.
                final_answer = verifier_output

            trace["iterations"].append(
                {
                    "step": step + 1,
                    "planner_prompt": planner_prompt,
                    "raw_plan": raw_plan,
                    "parsed_plan": plan,
                    "tool_results": tool_results,
                    "solver_prompt": solver_prompt,
                    "candidate_answer": candidate_answer,
                    "verifier_prompt": verifier_prompt,
                    "verifier_output": verifier_output,
                    "should_stop": should_stop,
                }
            )

            if should_stop:
                break

            verifier_feedback = verifier_output

        return {
            "agent": self.name,
            "final_output": final_answer,
            "trace": trace,
        }

    @staticmethod
    def _parse_plan(raw_plan: str) -> Dict[str, Any]:
        try:
            start = raw_plan.find("{")
            end = raw_plan.rfind("}")
            if start != -1 and end != -1:
                return json.loads(raw_plan[start:end + 1])
        except Exception:
            pass

        return {"tools": ["no_tool"]}

    @staticmethod
    def _should_stop(verifier_output: str) -> bool:
        return "status: correct" in verifier_output.lower()