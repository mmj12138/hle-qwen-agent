from __future__ import annotations

import json
import re
from typing import Any, Dict

from src.agents.base import chat
from src.agents.direct_agent import DirectAgent
from src.agents.tool_agent import ToolAgent
from src.prompts import (
    BASE_SOLVER_INSTRUCTIONS,
    SEARCH_ROUTER_PROMPT,
    SEARCH_SOLVER_PROMPT,
)
from src.search_web import TavilySearchError, TavilyWebSearch


class ToolSearchAgent:
    """Reuse ToolAgent's local-tool pipeline, then optionally use Tavily."""

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

        # Reuse exactly the same planner, tools, weak-hint filtering,
        # and exact-answer extraction as ToolAgent.
        tool_context = self.tool_agent.prepare_tool_context(
            question=question,
            answer_type=answer_type,
        )

        plan = tool_context["plan"]
        tool_results = tool_context["tool_results"]
        recommended_answer = tool_context["recommended_answer"]

        # Only an actual exact tool answer can terminate immediately.
        if recommended_answer:
            final_output = f"Final Answer: {recommended_answer}"
            return {
                "agent": self.name,
                "final_output": final_output,
                "trace": {
                    "tool_search_path": "deterministic_tool",
                    "dataset_category": category,
                    "parsed_plan": plan,
                    "tool_results": tool_results,
                    "real_tool_used": tool_context["real_tool_used"],
                    "weak_hints_only": tool_context["weak_hints_only"],
                    "recommended_answer": recommended_answer,
                    "search_used": False,
                    "final_output": final_output,
                },
            }

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
                tool_context=tool_context,
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
                tool_context=tool_context,
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
                tool_context=tool_context,
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
                tool_context=tool_context,
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
                "parsed_plan": plan,
                "tool_results": tool_results,
                "real_tool_used": tool_context["real_tool_used"],
                "weak_hints_only": tool_context["weak_hints_only"],
                "recommended_answer": "",
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
        parsed = _parse_router_output(raw_output)

        use_search = _coerce_bool(parsed.get("use_search", False))
        search_query = _clean_search_query(
            str(parsed.get("search_query", ""))
        )
        reason = str(parsed.get("reason", "")).strip()

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
                "parser": parsed.get("_parser", "unknown"),
            }

        if use_search and not search_query:
            search_query = _fallback_query(question)

        return {
            "use_search": bool(use_search and search_query),
            "reason": reason or "router_decision",
            "search_query": search_query if use_search else "",
            "raw_output": raw_output,
            "parser": parsed.get("_parser", "unknown"),
        }

    def _direct_fallback(
        self,
        llm,
        question: str,
        answer_type: str,
        category: str,
        tool_context: Dict[str, Any],
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
                "parsed_plan": tool_context["plan"],
                "tool_results": tool_context["tool_results"],
                "real_tool_used": tool_context["real_tool_used"],
                "weak_hints_only": tool_context["weak_hints_only"],
                "recommended_answer": "",
                "router_decision": router_decision,
                "search_used": False,
                "search_error": search_error,
                "search_output": search_output or {},
                "direct_result": direct_result,
            },
        }


def _parse_router_output(text: str) -> Dict[str, Any]:
    """Parse the preferred line format and tolerate legacy malformed JSON."""
    raw = str(text or "").strip()

    use_match = re.search(
        r"(?im)^\s*USE_SEARCH\s*:\s*(YES|NO|TRUE|FALSE|1|0)\s*$",
        raw,
    )
    query_match = re.search(
        r"(?im)^\s*SEARCH_QUERY\s*:\s*(.*?)\s*$",
        raw,
    )
    reason_match = re.search(
        r"(?im)^\s*REASON\s*:\s*(.*?)\s*$",
        raw,
    )

    if use_match:
        return {
            "use_search": _coerce_bool(use_match.group(1)),
            "search_query": query_match.group(1).strip() if query_match else "",
            "reason": reason_match.group(1).strip() if reason_match else "",
            "_parser": "line_format",
        }

    parsed_json = _extract_json_object(raw)
    if parsed_json is not None:
        parsed_json["_parser"] = "strict_json"
        return parsed_json

    bool_match = re.search(
        r'(?is)["\']?use_search["\']?\s*:\s*(true|false|yes|no|1|0)',
        raw,
    )
    json_query_match = re.search(
        r'(?is)["\']?search_query["\']?\s*:\s*["\'](.*?)(?<!\\)["\']'
        r'(?=\s*[,}\n]|$)',
        raw,
    )
    json_reason_match = re.search(
        r'(?is)["\']?reason["\']?\s*:\s*["\'](.*?)(?<!\\)["\']'
        r'(?=\s*,\s*["\']?search_query|\s*}\s*$)',
        raw,
    )

    if bool_match:
        return {
            "use_search": _coerce_bool(bool_match.group(1)),
            "search_query": (
                _unescape_router_text(json_query_match.group(1))
                if json_query_match
                else ""
            ),
            "reason": (
                _unescape_router_text(json_reason_match.group(1))
                if json_reason_match
                else "recovered_from_malformed_router_output"
            ),
            "_parser": "regex_recovery",
        }

    return {
        "use_search": False,
        "search_query": "",
        "reason": "router_output_unrecognized",
        "_parser": "unrecognized",
    }


def _extract_json_object(text: str) -> Dict[str, Any] | None:
    candidates = [text.strip()]

    fenced = re.search(
        r"```(?:json)?\s*(\{.*?\})\s*```",
        text,
        re.DOTALL | re.IGNORECASE,
    )
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


def _unescape_router_text(text: str) -> str:
    return (
        text.replace(r"\"", '"')
        .replace(r"\'", "'")
        .replace(r"\n", " ")
        .replace(r"\t", " ")
        .strip()
    )


def _clean_search_query(query: str) -> str:
    query = query.strip().strip("`").strip()
    query = re.sub(r"\s+", " ", query)
    return query[:300]


def _fallback_query(question: str) -> str:
    text = re.sub(r"\s+", " ", str(question or "")).strip()
    text = re.sub(
        r"(?i)\b(final answer|correct answer|gold answer|benchmark answer)\b",
        "",
        text,
    )
    return " ".join(text.split()[:32])[:300]


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {
            "true",
            "1",
            "yes",
            "y",
        }
    return bool(value)
