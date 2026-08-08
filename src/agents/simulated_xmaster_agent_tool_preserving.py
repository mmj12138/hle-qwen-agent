# Author: mmj
# Tool-preserving lightweight simulated X-Master agent
from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Tuple

from src.agents.base import chat
from src.agents.tool_agent import ToolAgent
from src.agents.tool_search_agent import ToolSearchAgent
from src.prompts import (
    SIM_XMASTER_SOLVER_PROMPT,
    SIM_XMASTER_CRITIC_PROMPT,
    SIM_XMASTER_SELECTOR_PROMPT,
)


class SimulatedXMasterToolPreAgent:
    """
    Tool-preserving X-Master-inspired ensemble.

    Main design:
        1. Run the existing ToolSearchAgent first.
        2. If ToolSearchAgent actually used a deterministic tool, accepted
           dynamic Python, or completed a web-search path, preserve its final
           answer exactly and stop.
        3. Only when ToolSearchAgent is effectively a plain fallback do we run
           independent candidates + critic + selector.

    This prevents the X-Master critic/selector from destroying answers that
    were already produced through the validated Tool/Search pipeline.

    Important:
    This guarantees preservation of *actual tool/search interventions*.
    It cannot mathematically guarantee total accuracy >= Tool accuracy on
    every sample without access to the gold answer, because fallback Tool
    answers may still be changed by the X-Master selector.
    """

    name = "sim_xmaster"

    def __init__(
        self,
        num_candidates: int = 3,
        max_tool_iterations: int = 2,
        use_search: bool = True,
        preserve_tool_interventions: bool = True,
    ):
        if num_candidates < 2:
            raise ValueError("num_candidates must be at least 2.")

        self.num_candidates = int(num_candidates)
        self.max_tool_iterations = int(max_tool_iterations)
        self.use_search = bool(use_search)
        self.preserve_tool_interventions = bool(
            preserve_tool_interventions
        )

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

        # ------------------------------------------------------------
        # Step 1: run the already validated Tool / ToolSearch pipeline.
        # ------------------------------------------------------------
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

        tool_locked, lock_reason = self._should_lock_tool_result(
            tool_result
        )

        # ------------------------------------------------------------
        # Step 2: preserve genuine tool/search interventions.
        # ------------------------------------------------------------
        if self.preserve_tool_interventions and tool_locked:
            final_output = tool_result["final_output"]

            return {
                "agent": self.name,
                "final_output": final_output,
                "trace": {
                    "num_candidates": self.num_candidates,
                    "num_independent_candidates": 0,
                    "tool_solver": self.tool_solver_name,
                    "tool_result": tool_result,
                    "tool_locked": True,
                    "tool_lock_reason": lock_reason,
                    "selection_source": "tool_locked",
                    "candidate_order": [
                        {
                            "candidate_index": 1,
                            "source": self.tool_solver_name,
                            "source_index": 1,
                        }
                    ],
                    "candidates": [
                        {
                            "candidate_index": 1,
                            "output": final_output,
                        }
                    ],
                    "critique": "",
                    "selector_output": "",
                    "final_selection": final_output,
                },
            }

        # ------------------------------------------------------------
        # Step 3: Tool was only a fallback. Now allow X-Master-style
        # multi-candidate reasoning to try to improve it.
        # ------------------------------------------------------------
        num_independent = self.num_candidates - 1

        raw_candidates: List[Dict[str, Any]] = []

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

        # Keep the Tool baseline as one candidate even when it was not locked.
        raw_candidates.append(
            {
                "source": self.tool_solver_name,
                "source_index": 1,
                "output": tool_result["final_output"],
                "trace": tool_result.get("trace", {}),
            }
        )

        # Deterministic rotation avoids always putting Tool in one position.
        candidates = self._rotate_candidates(
            raw_candidates,
            question,
        )
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
        selector_output = chat(llm, selector_prompt)
        final_output = selector_output

        return {
            "agent": self.name,
            "final_output": final_output,
            "trace": {
                "num_candidates": self.num_candidates,
                "num_independent_candidates": num_independent,
                "tool_solver": self.tool_solver_name,
                "tool_result": tool_result,
                "tool_locked": False,
                "tool_lock_reason": lock_reason,
                "selection_source": "xmaster_selector",
                "candidate_order": [
                    {
                        "candidate_index": index,
                        "source": candidate["source"],
                        "source_index": candidate["source_index"],
                    }
                    for index, candidate in enumerate(
                        candidates,
                        start=1,
                    )
                ],
                "candidates": [
                    {
                        "candidate_index": index,
                        "output": candidate["output"],
                    }
                    for index, candidate in enumerate(
                        candidates,
                        start=1,
                    )
                ],
                "critique": critique,
                "selector_output": selector_output,
                "final_selection": final_output,
            },
        }

    @classmethod
    def _should_lock_tool_result(
        cls,
        tool_result: Dict[str, Any],
    ) -> Tuple[bool, str]:
        """
        Protect answers that came from a real intervention.

        Lock when:
        - deterministic rule-based tool produced a real answer;
        - a completed web-search path was used;
        - dynamic Python was accepted by ToolAgent;
        - nested ToolAgent trace contains a real recommended/tool result.

        Do NOT lock ordinary direct/non-computational fallbacks.
        """
        trace = tool_result.get("trace", {})
        if not isinstance(trace, dict):
            return False, "missing_tool_trace"

        # 1. Deterministic local tools, e.g. knapsack, IP ACL, integer search.
        if trace.get("real_tool_used", False):
            return True, "deterministic_tool_used"

        if trace.get("recommended_answer"):
            return True, "deterministic_recommended_answer"

        tool_results = trace.get("tool_results")
        if isinstance(tool_results, dict) and tool_results:
            # Ignore weak hints if they did not actually produce an answer.
            if not trace.get("weak_hints_only", False):
                return True, "nonempty_tool_results"

        # 2. Completed web-search branch.
        #
        # This intentionally also protects "web_search_kept_direct":
        # ToolSearchAgent already compared search evidence against its local
        # candidate and deliberately decided to keep that answer.
        if trace.get("search_used", False):
            path = str(trace.get("tool_search_path", "web_search"))
            return True, path

        # 3. Dynamic Python or nested local ToolAgent interventions.
        for key in (
            "local_result",
            "local_tool_result",
            "direct_result",
        ):
            nested = trace.get(key)
            locked, reason = cls._inspect_nested_tool_result(
                nested,
                prefix=key,
            )
            if locked:
                return True, reason

        return False, "tool_fallback_only"

    @classmethod
    def _inspect_nested_tool_result(
        cls,
        result: Any,
        prefix: str,
    ) -> Tuple[bool, str]:
        if not isinstance(result, dict):
            return False, ""

        trace = result.get("trace")
        if not isinstance(trace, dict):
            return False, ""

        if trace.get("recommended_answer"):
            return True, f"{prefix}:recommended_answer"

        tool_results = trace.get("tool_results")
        if isinstance(tool_results, dict) and tool_results:
            return True, f"{prefix}:tool_results"

        if trace.get("python_answer_adopted", False):
            return True, f"{prefix}:python_answer_adopted"

        iterations = trace.get("iterations", [])
        if isinstance(iterations, list):
            for iteration in iterations:
                if not isinstance(iteration, dict):
                    continue

                mode = str(iteration.get("mode", "")).strip().lower()

                # "python_verified" is the current ToolAgent path when
                # generated Python executes and the verifier accepts it.
                if mode == "python_verified":
                    return True, f"{prefix}:python_verified"

                # Future-proof against similarly named accepted Python paths.
                if (
                    "python" in mode
                    and any(
                        token in mode
                        for token in (
                            "verified",
                            "adopted",
                            "accepted",
                            "executed",
                        )
                    )
                ):
                    return True, f"{prefix}:{mode}"

        return False, ""

    @staticmethod
    def _rotate_candidates(
        candidates: List[Dict[str, Any]],
        question: str,
    ) -> List[Dict[str, Any]]:
        if len(candidates) <= 1:
            return candidates

        digest = hashlib.sha256(
            question.encode("utf-8")
        ).digest()
        offset = (
            int.from_bytes(digest[:4], "big")
            % len(candidates)
        )

        return candidates[offset:] + candidates[:offset]

    @staticmethod
    def _format_candidates(
        candidates: List[Dict[str, Any]],
    ) -> str:
        blocks = []

        for index, candidate in enumerate(
            candidates,
            start=1,
        ):
            blocks.append(
                f"Candidate {index}:\n"
                f"{candidate['output'].strip()}"
            )

        return "\n\n".join(blocks)
