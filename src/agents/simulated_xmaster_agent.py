# Author: mmj
# Lightweight simulated X-Master agent:
# independent solvers + one tool/search solver + critic + final selector
from __future__ import annotations

import hashlib
from typing import Any, Dict, List

from src.agents.base import chat
from src.agents.tool_agent import ToolAgent
from src.agents.tool_search_agent import ToolSearchAgent
from src.prompts import (
    SIM_XMASTER_SOLVER_PROMPT,
    SIM_XMASTER_CRITIC_PROMPT,
    SIM_XMASTER_SELECTOR_PROMPT,
)


class SimulatedXMasterAgent:
    """
    Lightweight X-Master-inspired ensemble.

    Default workflow with num_candidates=3:
        1. Generate two independent LLM candidates.
        2. Generate one tool/search candidate.
        3. Anonymize and deterministically rotate candidate order.
        4. Ask a critic to assess all candidates.
        5. Ask a selector to produce the final concise answer.

    This is not the full X-Master implementation. It is an ablation-friendly
    approximation designed to test whether multi-candidate feedback and tools
    provide complementary gains.
    """

    name = "sim_xmaster"

    def __init__(
        self,
        num_candidates: int = 3,
        max_tool_iterations: int = 2,
        use_search: bool = True,
    ):
        if num_candidates < 2:
            raise ValueError("num_candidates must be at least 2.")

        self.num_candidates = int(num_candidates)
        self.max_tool_iterations = int(max_tool_iterations)
        self.use_search = bool(use_search)

        if self.use_search:
            self.tool_solver = ToolSearchAgent(
                max_iterations=self.max_tool_iterations
            )
            self.tool_solver_name = "tool_search"
        else:
            self.tool_solver = ToolAgent(
                max_iterations=self.max_tool_iterations
            )
            self.tool_solver_name = "tool"

    def run(
        self,
        llm,
        question: str,
        answer_type: str = "",
        category: str = "",
    ) -> Dict[str, Any]:
        answer_type = str(answer_type or "").strip()
        category = str(category or "unknown").strip()

        # Reserve exactly one candidate slot for the tool/search pipeline.
        num_independent = self.num_candidates - 1

        raw_candidates: List[Dict[str, Any]] = []

        # Independent candidates should not see one another.
        for solver_index in range(1, num_independent + 1):
            prompt = SIM_XMASTER_SOLVER_PROMPT.format(
                solver_index=solver_index,
                question=question,
                answer_type=answer_type or "unknown",
            )
            output = chat(llm, prompt)

            raw_candidates.append(
                {
                    "source": "independent_solver",
                    "source_index": solver_index,
                    "output": output,
                    "trace": {},
                }
            )

        # One candidate comes from the existing deterministic-tool/search
        # pipeline. This reuses the already validated ToolSearchAgent logic.
        if self.use_search:
            tool_result = self.tool_solver.run(
                llm,
                question=question,
                answer_type=answer_type,
                category=category,
            )
        else:
            tool_result = self.tool_solver.run(
                llm,
                question=question,
                answer_type=answer_type,
            )

        raw_candidates.append(
            {
                "source": self.tool_solver_name,
                "source_index": 1,
                "output": tool_result["final_output"],
                "trace": tool_result.get("trace", {}),
            }
        )

        # Avoid always placing the tool candidate last. Rotation is
        # deterministic, so repeated runs preserve candidate ordering.
        candidates = self._rotate_candidates(raw_candidates, question)
        formatted_candidates = self._format_candidates(candidates)

        critic_prompt = SIM_XMASTER_CRITIC_PROMPT.format(
            question=question,
            answer_type=answer_type or "unknown",
            category=category,
            candidates=formatted_candidates,
        )
        critique = chat(llm, critic_prompt)

        selector_prompt = SIM_XMASTER_SELECTOR_PROMPT.format(
            question=question,
            answer_type=answer_type or "unknown",
            category=category,
            candidates=formatted_candidates,
            critique=critique,
        )
        final_output = chat(llm, selector_prompt)

        return {
            "agent": self.name,
            "final_output": final_output,
            "trace": {
                "num_candidates": self.num_candidates,
                "num_independent_candidates": num_independent,
                "tool_solver": self.tool_solver_name,
                "candidate_order": [
                    {
                        "candidate_index": index,
                        "source": candidate["source"],
                        "source_index": candidate["source_index"],
                    }
                    for index, candidate in enumerate(candidates, start=1)
                ],
                "candidates": [
                    {
                        "candidate_index": index,
                        "output": candidate["output"],
                    }
                    for index, candidate in enumerate(candidates, start=1)
                ],
                "tool_result": tool_result,
                "critique": critique,
                "final_selection": final_output,
            },
        }

    @staticmethod
    def _rotate_candidates(
        candidates: List[Dict[str, Any]],
        question: str,
    ) -> List[Dict[str, Any]]:
        if len(candidates) <= 1:
            return candidates

        digest = hashlib.sha256(question.encode("utf-8")).digest()
        offset = int.from_bytes(digest[:4], "big") % len(candidates)
        return candidates[offset:] + candidates[:offset]

    @staticmethod
    def _format_candidates(
        candidates: List[Dict[str, Any]],
    ) -> str:
        blocks = []
        for index, candidate in enumerate(candidates, start=1):
            blocks.append(
                f"Candidate {index}:\n{candidate['output'].strip()}"
            )
        return "\n\n".join(blocks)
