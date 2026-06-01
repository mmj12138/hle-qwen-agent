# Author: mmj
# DATE: 30.05.2026
import json
from typing import Any, Dict

from src.prompts import (
    BASE_SOLVER_INSTRUCTIONS,
    TOOL_SOLVER_PROMPT,
    TOOL_VERIFIER_PROMPT,
)
from src.tools import (
    run_tools,
    rule_based_tool_plan,
    has_real_tool,
)
from src.agents.base import chat
from src.evaluator import extract_final_answer


class ToolAgent:
    name = "tool"

    def __init__(self, max_iterations: int = 2):
        self.max_iterations = max_iterations

    def run(self, llm, question: str, answer_type: str = "") -> Dict[str, Any]:
        plan = rule_based_tool_plan(question, answer_type=answer_type)
        tool_results = run_tools(plan, question, answer_type=answer_type)
        real_tool_used = has_real_tool(plan)

        trace = {
            "planner_type": "rule_based",
            "parsed_plan": plan,
            "tool_results": tool_results,
            "real_tool_used": real_tool_used,
            "iterations": [],
        }

        # If only answer_format_hint is available, do not run verifier loop.
        # This avoids answer drift on questions where tools add no real evidence.
        if not real_tool_used:
            solver_prompt = TOOL_SOLVER_PROMPT.format(
                question=question,
                tool_results=json.dumps(tool_results, ensure_ascii=False, indent=2),
                verifier_feedback="None.",
                base_instructions=BASE_SOLVER_INSTRUCTIONS,
            )
            candidate_answer = chat(llm, solver_prompt)

            trace["iterations"].append(
                {
                    "step": 1,
                    "mode": "format_only_direct",
                    "solver_prompt": solver_prompt,
                    "candidate_answer": candidate_answer,
                    "final_answer_for_this_step": candidate_answer,
                    "should_stop": True,
                }
            )

            return {
                "agent": self.name,
                "final_output": candidate_answer,
                "trace": trace,
            }

        verifier_feedback = "None."
        final_answer = ""

        for step in range(self.max_iterations):
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

            candidate_final = extract_final_answer(candidate_answer)
            verifier_final = extract_final_answer(verifier_output)

            # Conservative rule:
            # If verifier says incorrect but gives the same final answer,
            # it did not actually provide a better correction. Stop.
            same_final_answer = (
                candidate_final.strip().lower() == verifier_final.strip().lower()
                and candidate_final.strip() != ""
            )

            if should_stop or same_final_answer:
                final_answer = candidate_answer
                stop_reason = "verifier_correct" if should_stop else "same_final_answer"
                trace["iterations"].append(
                    {
                        "step": step + 1,
                        "mode": "real_tool_verify",
                        "solver_prompt": solver_prompt,
                        "candidate_answer": candidate_answer,
                        "verifier_prompt": verifier_prompt,
                        "verifier_output": verifier_output,
                        "candidate_final": candidate_final,
                        "verifier_final": verifier_final,
                        "same_final_answer": same_final_answer,
                        "final_answer_for_this_step": final_answer,
                        "should_stop": True,
                        "stop_reason": stop_reason,
                    }
                )
                break

            # If verifier really proposes a different answer, use it as feedback
            # for the next iteration, but do not immediately overwrite unless
            # max iterations is reached.
            final_answer = verifier_output
            verifier_feedback = verifier_output

            trace["iterations"].append(
                {
                    "step": step + 1,
                    "mode": "real_tool_verify",
                    "solver_prompt": solver_prompt,
                    "candidate_answer": candidate_answer,
                    "verifier_prompt": verifier_prompt,
                    "verifier_output": verifier_output,
                    "candidate_final": candidate_final,
                    "verifier_final": verifier_final,
                    "same_final_answer": same_final_answer,
                    "final_answer_for_this_step": final_answer,
                    "should_stop": False,
                    "stop_reason": "retry",
                }
            )

        return {
            "agent": self.name,
            "final_output": final_answer,
            "trace": trace,
        }

    @staticmethod
    def _should_stop(verifier_output: str) -> bool:
        return "status: correct" in verifier_output.lower()