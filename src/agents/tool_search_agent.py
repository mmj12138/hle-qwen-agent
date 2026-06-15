from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional

from src.agents.base import chat
from src.agents.direct_agent import DirectAgent
from src.agents.tool_agent import ToolAgent
from src.prompts import SEARCH_ROUTER_PROMPT, SEARCH_SOLVER_PROMPT
from src.search_web import TavilySearchError, TavilyWebSearch


# Conservative lexical guards. These prevent spending search credits on
# questions that require computation or direct inspection rather than factual
# retrieval from textual web sources.
_COMPUTATION_PATTERNS = (
    r"\bcalculate\b",
    r"\bcompute\b",
    r"\bderive\b",
    r"\bprove\b",
    r"\bnumber of solutions\b",
    r"\bhow many\b",
    r"\blargest prime\b",
    r"\bsmallest prime\b",
    r"\blargest integer\b",
    r"\bsmallest integer\b",
    r"\bmaximize\b",
    r"\bminimize\b",
    r"\bmodulo\b",
    r"\bdivisible\b",
    r"\bprobability of\b",
    r"\benumerat",
    r"\bcount\b",
)

_DIRECT_INSPECTION_PATTERNS = (
    r"\baudio\b",
    r"\brecording\b",
    r"\bseconds?\s+\d+",
    r"\btimestamp\b",
    r"\bmelody\b",
    r"\bnotes? played\b",
    r"\bshown in (?:the )?(?:image|figure|diagram|table)\b",
    r"\bimage\b",
    r"\bfigure\b",
    r"\bdiagram\b",
    r"\bchess position\b",
    r"\bfen\b",
)


class ToolSearchAgent:
    """Local deterministic tools + conservative Tavily retrieval."""

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
        answer_type = str(answer_type or "").strip()

        tool_context = self.tool_agent.prepare_tool_context(
            question=question,
            answer_type=answer_type,
        )
        recommended_answer = tool_context["recommended_answer"]

        # Exact deterministic answers remain the safest path.
        if recommended_answer:
            final_output = _format_final_answer(
                recommended_answer,
                answer_type,
            )
            return {
                "agent": self.name,
                "final_output": final_output,
                "trace": self._base_trace(
                    category=category,
                    tool_context=tool_context,
                    path="deterministic_tool",
                    search_used=False,
                    final_output=final_output,
                ),
            }

        blocked_reason = _pre_router_block_reason(question, category)
        if blocked_reason:
            return self._direct_fallback(
                llm=llm,
                question=question,
                answer_type=answer_type,
                category=category,
                tool_context=tool_context,
                router_decision={
                    "use_search": False,
                    "search_query": "",
                    "reason": blocked_reason,
                    "parser": "heuristic_guard",
                    "raw_output": "",
                },
                reason=blocked_reason,
            )

        router_decision = self._route_search(
            llm=llm,
            question=question,
            answer_type=answer_type,
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

        query = router_decision["search_query"]
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

        results = search_output.get("results") or []
        if not results:
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
            answer_type=answer_type or "unknown",
            category=category,
            search_evidence=evidence,
        )
        raw_search_answer = chat(llm, solver_prompt)

        # The model is explicitly allowed to reject insufficient evidence.
        if _is_insufficient_evidence(raw_search_answer):
            return self._direct_fallback(
                llm=llm,
                question=question,
                answer_type=answer_type,
                category=category,
                tool_context=tool_context,
                router_decision=router_decision,
                reason="insufficient_search_evidence",
                search_output=search_output,
                raw_search_answer=raw_search_answer,
            )

        normalized_answer = _normalize_search_answer(
            raw_search_answer,
            answer_type,
        )
        if normalized_answer is None:
            return self._direct_fallback(
                llm=llm,
                question=question,
                answer_type=answer_type,
                category=category,
                tool_context=tool_context,
                router_decision=router_decision,
                reason="unparseable_search_answer",
                search_output=search_output,
                raw_search_answer=raw_search_answer,
            )

        final_output = _format_final_answer(
            normalized_answer,
            answer_type,
        )
        trace = self._base_trace(
            category=category,
            tool_context=tool_context,
            path="web_search",
            search_used=True,
            final_output=final_output,
        )
        trace.update(
            {
                "router_decision": router_decision,
                "search_query": query,
                "search_output": search_output,
                "possible_leakage_check": leakage_check,
                "raw_search_answer": raw_search_answer,
                "normalized_search_answer": normalized_answer,
            }
        )

        return {
            "agent": self.name,
            "final_output": final_output,
            "trace": trace,
        }

    def _route_search(
        self,
        llm,
        question: str,
        answer_type: str,
        category: str,
    ) -> Dict[str, Any]:
        prompt = SEARCH_ROUTER_PROMPT.format(
            question=question,
            answer_type=answer_type or "unknown",
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
            use_search = False
            search_query = ""
            reason = "unsafe_or_leakage_seeking_query"

        # Do not silently invent a query. Missing query now means no search.
        if use_search and not search_query:
            use_search = False
            reason = "router_selected_search_without_query"

        return {
            "use_search": bool(use_search),
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
        search_output: Optional[Dict[str, Any]] = None,
        raw_search_answer: str = "",
    ) -> Dict[str, Any]:
        direct_result = self.direct_agent.run(
            llm,
            question=question,
            answer_type=answer_type,
        )

        trace = self._base_trace(
            category=category,
            tool_context=tool_context,
            path="direct_fallback",
            search_used=False,
            final_output=direct_result["final_output"],
        )
        trace.update(
            {
                "fallback_reason": reason,
                "router_decision": router_decision,
                "search_error": search_error,
                "search_output": search_output or {},
                "raw_search_answer": raw_search_answer,
                "direct_result": direct_result,
            }
        )

        return {
            "agent": self.name,
            "final_output": direct_result["final_output"],
            "trace": trace,
        }

    @staticmethod
    def _base_trace(
        category: str,
        tool_context: Dict[str, Any],
        path: str,
        search_used: bool,
        final_output: str,
    ) -> Dict[str, Any]:
        return {
            "tool_search_path": path,
            "dataset_category": category,
            "parsed_plan": tool_context["plan"],
            "tool_results": tool_context["tool_results"],
            "real_tool_used": tool_context["real_tool_used"],
            "weak_hints_only": tool_context["weak_hints_only"],
            "recommended_answer": tool_context["recommended_answer"],
            "search_used": search_used,
            "final_output": final_output,
        }


def _pre_router_block_reason(question: str, category: str) -> str:
    text = re.sub(r"\s+", " ", question).lower()

    if any(re.search(pattern, text) for pattern in _DIRECT_INSPECTION_PATTERNS):
        return "direct_inspection_required"

    # Mathematical and CS questions with explicit computational wording should
    # not be sent to web search. Named-theorem or definition questions are not
    # blocked unless they also match these computational cues.
    if category.lower() in {"math", "computer science/ai", "engineering"}:
        if any(re.search(pattern, text) for pattern in _COMPUTATION_PATTERNS):
            return "computation_or_derivation_required"

    return ""


def _is_insufficient_evidence(text: str) -> bool:
    normalized = re.sub(r"\s+", " ", str(text or "")).strip().upper()
    return normalized == "EVIDENCE_INSUFFICIENT" or (
        "EVIDENCE_INSUFFICIENT" in normalized
    )


def _normalize_search_answer(
    text: str,
    answer_type: str,
) -> Optional[str]:
    raw = str(text or "").strip()
    if not raw:
        return None

    # Use the final occurrence to repair duplicated prefixes.
    matches = list(
        re.finditer(
            r"(?is)final\s+answer\s*:\s*(.+)",
            raw,
        )
    )
    answer = matches[-1].group(1).strip() if matches else raw

    # Remove an accidentally repeated prefix.
    answer = re.sub(
        r"(?is)^final\s+answer\s*:\s*",
        "",
        answer,
    ).strip()

    # Search output must be concise; multiline explanations are rejected.
    answer = answer.splitlines()[0].strip()
    answer = answer.strip("`*_ ")

    if not answer:
        return None

    if _is_multiple_choice(answer_type):
        match = re.fullmatch(
            r"(?:option\s*)?\(?([A-F])\)?[.\s]*",
            answer,
            flags=re.IGNORECASE,
        )
        return match.group(1).upper() if match else None

    # Reject obvious refusal/uncertainty prose instead of scoring it as an answer.
    lower = answer.lower()
    invalid_markers = (
        "not available",
        "cannot determine",
        "insufficient",
        "further analysis",
        "there is no",
        "depends on",
        "based on the provided",
    )
    if any(marker in lower for marker in invalid_markers):
        return None

    # Exact-match answers should still be short.
    if len(answer) > 180:
        return None

    return answer


def _format_final_answer(answer: str, answer_type: str) -> str:
    cleaned = re.sub(
        r"(?is)^final\s+answer\s*:\s*",
        "",
        str(answer or "").strip(),
    ).strip()
    return f"Final Answer: {cleaned}"


def _is_multiple_choice(answer_type: str) -> bool:
    normalized = str(answer_type or "").lower()
    return "multiple" in normalized or normalized in {
        "mcq",
        "choice",
        "multiple_choice",
    }


def _parse_router_output(text: str) -> Dict[str, Any]:
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


def _extract_json_object(text: str) -> Optional[Dict[str, Any]]:
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
    return query[:240]


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
