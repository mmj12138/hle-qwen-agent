from __future__ import annotations

import json
import re
from typing import Any, Dict

from src.agents.base import chat
from src.agents.direct_agent import DirectAgent
from src.prompts import BASE_SOLVER_INSTRUCTIONS, SEARCH_SOLVER_PROMPT, SEARCH_ROUTER_PROMPT
from src.search_web import TavilySearchError, TavilyWebSearch
from src.tools import (
    extract_recommended_final_answer,
    rule_based_tool_plan,
    run_tools,
)

class ToolSearchAgent:
    """Deterministic tools + LLM-routed Tavily search.

    Routing order:
      1. Run matching local tools.
      2. Use the deterministic path only when a tool returns an exact
         ``Recommended final answer``.
      3. Otherwise ask the LLM router whether web search is useful.
      4. Fall back to DirectAgent when search is unnecessary or unavailable.
    """

    name = "tool_search"

    def __init__(self, max_iterations: int = 2):
        self.max_iterations = max_iterations
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
        deterministic_results = run_tools(
            deterministic_plan,
            question,
            answer_type=answer_type,
        )
        recommended_answer = extract_recommended_final_answer(
            deterministic_results
        ).strip()

        # A tool match alone is not enough. It must produce an exact answer.
        # This prevents false deterministic routing such as:
        # - Caesar tool with empty input
        # - controlled_math_tool returning only a weak hint
        if recommended_answer:
            final_output = f"Final Answer: {recommended_answer}"
            return {
                "agent": self.name,
                "final_output": final_output,
                "trace": {
                    "tool_search_path": "deterministic_tool",
                    "dataset_category": category,
                    "deterministic_plan": deterministic_plan,
                    "deterministic_tool_results": deterministic_results,
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
                deterministic_plan=deterministic_plan,
                deterministic_results=deterministic_results,
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
                deterministic_plan=deterministic_plan,
                deterministic_results=deterministic_results,
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
                deterministic_plan=deterministic_plan,
                deterministic_results=deterministic_results,
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
                deterministic_plan=deterministic_plan,
                deterministic_results=deterministic_results,
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
                "deterministic_tool_results": deterministic_results,
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

        # If the router says YES but omits the query, use a conservative
        # compact query derived from the question instead of silently falling
        # back because of formatting failure.
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
        deterministic_plan: Dict[str, Any],
        deterministic_results: Dict[str, Any],
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
                "deterministic_plan": deterministic_plan,
                "deterministic_tool_results": deterministic_results,
                "recommended_answer": "",
                "router_decision": router_decision,
                "search_used": False,
                "search_error": search_error,
                "search_output": search_output or {},
                "direct_result": direct_result,
            },
        }


def _parse_router_output(text: str) -> Dict[str, Any]:
    """Parse both the new three-line format and imperfect legacy JSON.

    The fallback parser intentionally tolerates:
    - a missing final ``}``;
    - invalid JSON backslash escapes from LaTeX;
    - fenced JSON;
    - extra prose around the structured response.
    """
    raw = str(text or "").strip()

    # 1. Preferred line-based format.
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

    # 2. Strict JSON when the model follows the old prompt.
    parsed_json = _extract_json_object(raw)
    if parsed_json is not None:
        parsed_json["_parser"] = "strict_json"
        return parsed_json

    # 3. Recover individual fields from incomplete/invalid JSON.
    json_bool_match = re.search(
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

    if json_bool_match:
        return {
            "use_search": _coerce_bool(json_bool_match.group(1)),
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

    # Conservative default: do not spend a search credit when the model
    # produced no recognizable routing decision.
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
    # Do not decode arbitrary escapes. Only normalize formatting escapes
    # commonly produced by the model.
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
    """Create a compact fallback query without benchmark-answer language."""
    text = re.sub(r"\s+", " ", str(question or "")).strip()
    text = re.sub(
        r"(?i)\b(final answer|correct answer|gold answer|benchmark answer)\b",
        "",
        text,
    )

    # Keep enough context for a useful search while avoiding a full long prompt.
    words = text.split()
    return " ".join(words[:32])[:300]


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
