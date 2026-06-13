from __future__ import annotations

import json
import re
from typing import Any, Dict

from src.agents.base import chat
from src.agents.direct_agent import DirectAgent
from src.agents.tool_agent import ToolAgent
from src.prompts import BASE_SOLVER_INSTRUCTIONS, SEARCH_ROUTER_PROMPT, SEARCH_SOLVER_PROMPT
from src.search_web import TavilyWebSearch, TavilySearchError
from src.tools import has_real_tool, rule_based_tool_plan


class ToolSearchAgent:
    """Deterministic Tool Agent + LLM-routed Tavily web search.

    Routing order:
      1. Existing deterministic tool router.
      2. LLM semantic decision about web search, using category as auxiliary data.
      3. DirectAgent fallback.
    """

    name = "tool_search"

    def __init__(self, max_iterations: int = 2):
        self.max_iterations = max_iterations
        self.tool_agent = ToolAgent(max_iterations=max_iterations)
        self.direct_agent = DirectAgent()
        self.search_client = TavilyWebSearch()

    def run(
        self,
        llm,
        question: str,
        answer_type: str = "",
        category: str = "",
    ) -> Dict[str, Any]:
        category = str(category or "unknown").strip()

        deterministic_plan = rule_based_tool_plan(
            question,
            answer_type=answer_type,
        )

        # Preserve the existing deterministic ToolAgent exactly.
        if has_real_tool(deterministic_plan):
            result = self.tool_agent.run(
                llm,
                question=question,
                answer_type=answer_type,
            )
            result["agent"] = self.name
            result.setdefault("trace", {})
            result["trace"]["tool_search_path"] = "deterministic_tool"
            result["trace"]["dataset_category"] = category
            result["trace"]["search_used"] = False
            return result

        router_decision = self._route_search(
            llm=llm,
            question=question,
            category=category,
        )

        if not router_decision["use_search"]:
            return self._direct_fallback(
                llm=llm,
                question=question,
                answer_type=answer_type,
                category=category,
                router_decision=router_decision,
                reason="router_selected_direct",
            )

        query = router_decision["search_query"].strip()
        if not query:
            return self._direct_fallback(
                llm=llm,
                question=question,
                answer_type=answer_type,
                category=category,
                router_decision=router_decision,
                reason="empty_search_query",
            )

        try:
            search_output = self.search_client.search(query)
        except TavilySearchError as exc:
            return self._direct_fallback(
                llm=llm,
                question=question,
                answer_type=answer_type,
                category=category,
                router_decision=router_decision,
                reason="search_error",
                search_error=str(exc),
            )

        if not search_output.get("results"):
            return self._direct_fallback(
                llm=llm,
                question=question,
                answer_type=answer_type,
                category=category,
                router_decision=router_decision,
                reason="no_search_results",
                search_output=search_output,
            )

        evidence = self.search_client.format_evidence(search_output)
        leakage_check = self.search_client.detect_possible_leakage(
            question,
            search_output,
        )

        solver_prompt = SEARCH_SOLVER_PROMPT.format(
            question=question,
            category=category,
            search_evidence=evidence,
            base_instructions=BASE_SOLVER_INSTRUCTIONS,
        )
        final_output = chat(llm, solver_prompt)

        return {
            "agent": self.name,
            "final_output": final_output,
            "trace": {
                "tool_search_path": "web_search",
                "dataset_category": category,
                "deterministic_plan": deterministic_plan,
                "router_decision": router_decision,
                "search_used": True,
                "search_query": query,
                "search_output": search_output,
                "possible_leakage_check": leakage_check,
                "solver_prompt": solver_prompt,
                "final_output": final_output,
            },
        }

    def _route_search(
        self,
        llm,
        question: str,
        category: str,
    ) -> Dict[str, Any]:
        prompt = SEARCH_ROUTER_PROMPT.format(
            question=question,
            category=category,
        )
        raw_output = chat(llm, prompt)
        parsed = _extract_json_object(raw_output)

        if parsed is None:
            return {
                "use_search": False,
                "reason": "router_json_parse_failed",
                "search_query": "",
                "raw_output": raw_output,
            }

        use_search = _coerce_bool(parsed.get("use_search", False))
        search_query = str(parsed.get("search_query", "")).strip()
        reason = str(parsed.get("reason", "")).strip()

        # Defensive cleaning: do not let the router explicitly search for gold answers.
        forbidden = (
            "hle answer",
            "benchmark answer",
            "gold answer",
            "correct answer",
        )
        if any(term in search_query.lower() for term in forbidden):
            return {
                "use_search": False,
                "reason": "unsafe_or_leakage_seeking_query",
                "search_query": "",
                "raw_output": raw_output,
            }

        return {
            "use_search": bool(use_search and search_query),
            "reason": reason or "router_decision",
            "search_query": search_query if use_search else "",
            "raw_output": raw_output,
        }

    def _direct_fallback(
        self,
        llm,
        question: str,
        answer_type: str,
        category: str,
        router_decision: Dict[str, Any],
        reason: str,
        search_error: str = "",
        search_output: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        direct_result = self.direct_agent.run(
            llm,
            question=question,
            answer_type=answer_type,
        )

        return {
            "agent": self.name,
            "final_output": direct_result["final_output"],
            "trace": {
                "tool_search_path": "direct_fallback",
                "fallback_reason": reason,
                "dataset_category": category,
                "router_decision": router_decision,
                "search_used": False,
                "search_error": search_error,
                "search_output": search_output or {},
                "direct_result": direct_result,
            },
        }


def _extract_json_object(text: str) -> Dict[str, Any] | None:
    text = text.strip()
    candidates = [text]

    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        candidates.insert(0, fenced.group(1))

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        candidates.append(text[start : end + 1])

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue
    return None


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)
