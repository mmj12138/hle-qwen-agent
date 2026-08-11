# Author: mmj
# Python-enabled conservative ToolAgent
from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Optional

from src.prompts import (
    PYTHON_PROGRAMMER_PROMPT,
    PYTHON_RESULT_VERIFIER_PROMPT,
)
from src.tools import (
    run_tools,
    rule_based_tool_plan,
    extract_recommended_final_answer,
    has_real_tool,
)
from src.python_executor import (
    PythonExecutor,
    extract_python_final_answer,
)
from src.agents.base import chat
from src.agents.direct_agent import DirectAgent


PYTHON_PROGRAMMER_MAX_NEW_TOKENS = int(
    os.getenv("PYTHON_PROGRAMMER_MAX_NEW_TOKENS", "512")
)
PYTHON_VERIFIER_MAX_NEW_TOKENS = int(
    os.getenv("PYTHON_VERIFIER_MAX_NEW_TOKENS", "96")
)



class ToolAgent:
    name = "tool"

    def __init__(self, max_iterations: int = 2):
        self.max_iterations = max_iterations
        self.python_executor = PythonExecutor()

    def prepare_tool_context(
            self,
            question: str,
            answer_type: str = "",
    ) -> Dict[str, Any]:
        """Run deterministic tools and return reusable tool context."""

        plan = rule_based_tool_plan(
            question,
            answer_type=answer_type,
        )

        tools = plan.get("tools", [])
        if isinstance(tools, str):
            tools = [tools]

        tool_results = (
            run_tools(
                plan,
                question,
                answer_type=answer_type,
            )
            if tools
            else {}
        )

        recommended_answer = extract_recommended_final_answer(
            tool_results
        )
        recommended_answer = str(
            recommended_answer or ""
        ).strip()

        real_tool_used = has_real_tool(plan)

        weak_hint_markers = (
            "use this as a hint only",
            "no exact controlled math template matched",
            "no exact controlled template matched",
            "no supported exact",
            "no recommended final answer",
            "no text provided",
            "no expression provided",
        )

        non_format_results = [
            str(value).lower()
            for key, value in tool_results.items()
            if key != "answer_format_hint"
        ]

        weak_hints_only = bool(non_format_results) and all(
            any(
                marker in result
                for marker in weak_hint_markers
            )
            for result in non_format_results
        )

        if weak_hints_only:
            real_tool_used = False

        return {
            "plan": plan,
            "tools": tools,
            "tool_results": tool_results,
            "recommended_answer": recommended_answer,
            "real_tool_used": real_tool_used,
            "weak_hints_only": weak_hints_only,
            "tool_success": (
                real_tool_used
                or bool(recommended_answer)
            ),
        }

    def run(
        self,
        llm,
        question: str,
        answer_type: str = "",
    ) -> Dict[str, Any]:
        # ----------------------------------------------------------
        # 1. Existing deterministic rule-based tools
        # ----------------------------------------------------------
        context = self.prepare_tool_context(
            question=question,
            answer_type=answer_type,
        )

        plan = context["plan"]
        tools = context["tools"]
        tool_results = context["tool_results"]
        recommended_answer = context["recommended_answer"]

        trace: Dict[str, Any] = {
            "planner_type": "rule_based_then_python",
            "parsed_plan": plan,
            "tool_results": tool_results,
            "recommended_answer": recommended_answer,
            "iterations": [],
        }

        if recommended_answer:
            final_output = (
                f"Final Answer: {recommended_answer}"
            )
            trace["iterations"].append(
                {
                    "step": 1,
                    "mode": "deterministic_tool_direct",
                    "recommended_answer": recommended_answer,
                    "should_stop": True,
                }
            )
            return {
                "agent": self.name,
                "final_output": final_output,
                "trace": trace,
            }

        # Always create the baseline candidate before considering
        # generated Python. This prevents weak tools from causing drift.
        direct_result = DirectAgent().run(
            llm,
            question=question,
            answer_type=answer_type,
        )
        direct_answer = _normalize_candidate(
            direct_result.get("final_output", ""),
            answer_type,
        )

        trace["direct_result"] = direct_result
        trace["direct_candidate"] = direct_answer

        # Dynamic Python is temporarily disabled for multiple-choice questions.
        # Existing deterministic tools above are still allowed to answer MCQs.
        if _is_multiple_choice(answer_type):
            trace["iterations"].append(
                {
                    "step": 1,
                    "mode": "python_skipped_multiple_choice",
                    "should_stop": True,
                }
            )
            return {
                "agent": self.name,
                "final_output": direct_result["final_output"],
                "trace": trace,
            }

        # ----------------------------------------------------------
        # 2. Cheap conservative pre-router
        # ----------------------------------------------------------
        if not _looks_computational(question):
            trace["iterations"].append(
                {
                    "step": 1,
                    "mode": "direct_fallback_noncomputational",
                    "should_stop": True,
                }
            )
            return {
                "agent": self.name,
                "final_output": direct_result["final_output"],
                "trace": trace,
            }

        # ----------------------------------------------------------
        # 3. Ask the model for a short deterministic Python program
        # ----------------------------------------------------------
        programmer_prompt = PYTHON_PROGRAMMER_PROMPT.format(
            question=question,
            answer_type=answer_type or "unknown",
        )
        programmer_output = _chat_with_token_limit(
            llm,
            programmer_prompt,
            max_new_tokens=PYTHON_PROGRAMMER_MAX_NEW_TOKENS,
        )
        use_python, reason, python_code = _parse_programmer_output(
            programmer_output
        )

        trace["python_programmer_prompt"] = programmer_prompt
        trace["python_programmer_max_new_tokens"] = (
            PYTHON_PROGRAMMER_MAX_NEW_TOKENS
        )
        trace["python_programmer_output"] = programmer_output
        trace["python_router_use"] = use_python
        trace["python_router_reason"] = reason
        trace["python_code"] = python_code

        if not use_python or not python_code:
            trace["iterations"].append(
                {
                    "step": 1,
                    "mode": "python_router_kept_direct",
                    "should_stop": True,
                    "reason": reason,
                }
            )
            return {
                "agent": self.name,
                "final_output": direct_result["final_output"],
                "trace": trace,
            }

        # ----------------------------------------------------------
        # 4. Execute in an isolated resource-limited subprocess
        # ----------------------------------------------------------
        execution = self.python_executor.run(python_code)
        python_answer = (
            extract_python_final_answer(execution.stdout)
            if execution.ok
            else ""
        )
        python_answer = _normalize_candidate(
            python_answer,
            answer_type,
        )

        trace["python_execution"] = {
            "ok": execution.ok,
            "stdout": execution.stdout,
            "stderr": execution.stderr,
            "returncode": execution.returncode,
            "error": execution.error,
        }
        trace["python_candidate"] = python_answer

        if not execution.ok or not python_answer:
            trace["iterations"].append(
                {
                    "step": 1,
                    "mode": "python_execution_failed_keep_direct",
                    "should_stop": True,
                    "error": execution.error,
                }
            )
            return {
                "agent": self.name,
                "final_output": direct_result["final_output"],
                "trace": trace,
            }

        if (
            direct_answer is not None
            and _answers_equivalent(
                direct_answer,
                python_answer,
                answer_type,
            )
        ):
            trace["iterations"].append(
                {
                    "step": 1,
                    "mode": "python_direct_agree",
                    "should_stop": True,
                }
            )
            return {
                "agent": self.name,
                "final_output": direct_result["final_output"],
                "trace": trace,
            }

        # ----------------------------------------------------------
        # 5. Conservative candidate arbitration
        # ----------------------------------------------------------
        verifier_prompt = PYTHON_RESULT_VERIFIER_PROMPT.format(
            question=question,
            answer_type=answer_type or "unknown",
            direct_answer=direct_answer or "",
            python_code=python_code,
            python_stdout=execution.stdout,
            python_answer=python_answer,
        )
        verifier_output = _chat_with_token_limit(
            llm,
            verifier_prompt,
            max_new_tokens=PYTHON_VERIFIER_MAX_NEW_TOKENS,
        )
        verifier = _parse_verifier_output(
            verifier_output,
            answer_type,
        )

        use_python_answer = (
            verifier["decision"] == "USE_PYTHON"
            and verifier["selected_answer"] is not None
            and _answers_equivalent(
                verifier["selected_answer"],
                python_answer,
                answer_type,
            )
        )

        trace["python_verifier_prompt"] = verifier_prompt
        trace["python_verifier_max_new_tokens"] = (
            PYTHON_VERIFIER_MAX_NEW_TOKENS
        )
        trace["python_verifier_output"] = verifier_output
        trace["python_verifier_decision"] = verifier["decision"]
        trace["python_verifier_reason"] = verifier["reason"]
        trace["python_answer_adopted"] = use_python_answer

        selected = (
            python_answer
            if use_python_answer
            else direct_answer
        )

        if selected is None:
            selected = python_answer

        final_output = f"Final Answer: {selected}"
        trace["iterations"].append(
            {
                "step": 1,
                "mode": (
                    "python_verified"
                    if use_python_answer
                    else "python_kept_direct"
                ),
                "should_stop": True,
            }
        )

        return {
            "agent": self.name,
            "final_output": final_output,
            "trace": trace,
        }


def _chat_with_token_limit(
    llm,
    prompt: str,
    max_new_tokens: int,
) -> str:
    """Call the existing chat function with a temporary token budget.

    Direct and other agents keep the global MAX_NEW_TOKENS value. Only this
    single call receives the larger programmer/verifier budget.
    """
    config = getattr(llm, "config", None)
    if config is None or not hasattr(config, "max_new_tokens"):
        return chat(llm, prompt)

    original = config.max_new_tokens
    try:
        config.max_new_tokens = int(max_new_tokens)
        return chat(llm, prompt)
    finally:
        config.max_new_tokens = original


def _looks_computational(question: str) -> bool:
    q = re.sub(r"\s+", " ", str(question or "")).lower()

    # 明显需要外部知识、理论证明或专业概念，不交给 Python。
    reject_patterns = (
        r"\bprove\b",
        r"\btheorem\b",
        r"\bmoduli space\b",
        r"\bhomology\b",
        r"\bmanifold\b",
        r"\btopolog",
        r"\baccording to\b",
        r"\bwhich statements?\b",
        r"\bidentify the correct\b",
        r"\bconcept\b",
        r"\bdefinition\b",
        r"\brubik",
        r"\bchess\b",
        r"\bgame of life\b",
        r"\bgraphical models?\b",
        r"\bimitation learning\b",
        r"\binformation theory\b",
        r"\bmutual information\b",
        r"\bupper bound\b",
        r"\blower bound\b",
        r"\btightest bound\b",
    )

    if any(re.search(pattern, q) for pattern in reject_patterns):
        return False

    # 必须出现明确的算法或有限计算信号。
    strong_patterns = (
        r"\bmodulo\b",
        r"\bdivisib",
        r"\bprime\b",
        r"\bfactor(?:ization)?\b",
        r"\bgcd\b",
        r"\blcm\b",
        r"\brecurrence\b",
        r"\bfinite enumeration\b",
        r"\benumerate all\b",
        r"\bpermutation\b",
        r"\bcombination\b",
        r"\bsubset sum\b",
        r"\bknapsack\b",
        r"\bshortest path\b",
        r"\bmaximum flow\b",
        r"\bminimum spanning tree\b",
        r"\bmatching\b",
        r"\bdynamic programming\b",
        r"\btiling\b",
        r"\bbinary states?\b",
        r"\bbase[- ]\d+\b",
        r"\bpalindrome\b",
        r"\bsolve\b.{0,40}=",
    )

    if any(re.search(pattern, q) for pattern in strong_patterns):
        return True

    # 普通数值题必须同时有明确数字和计算动作。
    has_number = bool(
        re.search(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?", q)
    )

    numerical_action = any(
        re.search(pattern, q)
        for pattern in (
            r"\bcalculate\b",
            r"\bcompute\b",
            r"\bevaluate\b",
            r"\bfind the exact value\b",
            r"\bnumber of ways\b",
            r"\bexpected number\b",
            r"\bexpected waiting time\b",
        )
    )

    return has_number and numerical_action


def _parse_programmer_output(
    text: str,
) -> tuple[bool, str, str]:
    raw = str(text or "").strip()

    use_match = re.search(
        r"(?im)^\s*USE_PYTHON\s*:\s*(YES|NO)\s*$",
        raw,
    )
    reason_match = re.search(
        r"(?im)^\s*REASON\s*:\s*(.*?)\s*$",
        raw,
    )

    use_python = (
        bool(use_match)
        and use_match.group(1).upper() == "YES"
    )

    reason = (
        reason_match.group(1).strip()
        if reason_match
        else "unparsed_programmer_reason"
    )

    if not use_python:
        return False, reason, ""

    # Require an explicit description of the inputs, target, and algorithm.
    inputs_match = re.search(
        r"(?im)^\s*INPUTS\s*:\s*(.*?)\s*$",
        raw,
    )
    target_match = re.search(
        r"(?im)^\s*TARGET\s*:\s*(.*?)\s*$",
        raw,
    )
    algorithm_match = re.search(
        r"(?im)^\s*ALGORITHM\s*:\s*(.*?)\s*$",
        raw,
    )

    if not inputs_match:
        return False, "missing_explicit_inputs", ""

    if not target_match:
        return False, "missing_explicit_target", ""

    if not algorithm_match:
        return False, "missing_explicit_algorithm", ""

    inputs_text = inputs_match.group(1).strip()
    target_text = target_match.group(1).strip()
    algorithm_text = algorithm_match.group(1).strip()

    invalid_values = {
        "",
        "none",
        "n/a",
        "na",
        "unknown",
        "not specified",
        "not provided",
        "no explicit inputs",
        "no inputs",
        "missing",
    }

    if inputs_text.lower() in invalid_values:
        return False, "invalid_explicit_inputs", ""

    if target_text.lower() in invalid_values or len(target_text) < 5:
        return False, "invalid_explicit_target", ""

    if algorithm_text.lower() in invalid_values or len(algorithm_text) < 5:
        return False, "invalid_explicit_algorithm", ""

    # Preferred: complete fenced Python code block.
    complete_match = re.search(
        r"```(?:python)?\s*(.*?)```",
        raw,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if complete_match:
        code = complete_match.group(1).strip()

        if not code:
            return False, "empty_python_code", ""

        return True, reason, code

    # Recovery: the model may reach its token limit after opening
    # the code fence. The executor will perform AST validation.
    open_match = re.search(
        r"```(?:python)?\s*(.*)\Z",
        raw,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if open_match:
        recovered = open_match.group(1).strip()
        recovered = re.sub(
            r"\n?`{1,3}\s*\Z",
            "",
            recovered,
        ).strip()

        if not recovered:
            return False, "empty_python_code", ""

        return True, reason, recovered

    return False, "missing_python_code", ""

def _normalize_candidate(
    text: str,
    answer_type: str,
) -> Optional[str]:
    raw = str(text or "").strip()
    if not raw:
        return None

    matches = list(
        re.finditer(
            r"(?is)(?:final_answer|final\s+answer)\s*:\s*(.+)",
            raw,
        )
    )
    value = matches[-1].group(1).strip() if matches else raw
    value = value.splitlines()[0].strip()
    value = value.strip("`*_ ")

    if not value:
        return None

    if _is_multiple_choice(answer_type):
        match = re.fullmatch(
            r"(?:option\s*)?\(?([A-F])\)?[.\s]*",
            value,
            flags=re.IGNORECASE,
        )
        return match.group(1).upper() if match else None

    if len(value) > 200:
        return None

    return value


def _parse_verifier_output(
    text: str,
    answer_type: str,
) -> Dict[str, Any]:
    raw = str(text or "").strip()

    decision_match = re.search(
        r"(?im)^\s*DECISION\s*:\s*"
        r"(KEEP_DIRECT|USE_PYTHON)\s*$",
        raw,
    )
    answer_match = re.search(
        r"(?im)^\s*FINAL_ANSWER\s*:\s*(.*?)\s*$",
        raw,
    )
    reason_match = re.search(
        r"(?im)^\s*REASON\s*:\s*(.*?)\s*$",
        raw,
    )

    if not decision_match:
        return {
            "decision": "KEEP_DIRECT",
            "selected_answer": None,
            "reason": "verifier_output_unrecognized",
        }

    selected = (
        _normalize_candidate(
            answer_match.group(1),
            answer_type,
        )
        if answer_match
        else None
    )

    return {
        "decision": decision_match.group(1).upper(),
        "selected_answer": selected,
        "reason": (
            reason_match.group(1).strip()
            if reason_match
            else "parsed_without_reason"
        ),
    }


def _answers_equivalent(
    left: str,
    right: str,
    answer_type: str,
) -> bool:
    if _is_multiple_choice(answer_type):
        return left.strip().upper() == right.strip().upper()

    def canonical(value: str) -> str:
        value = value.casefold()
        value = re.sub(r"\s+", " ", value)
        return value.strip(" .,:;!?\"'`")

    return canonical(left) == canonical(right)


def _is_multiple_choice(answer_type: str) -> bool:
    normalized = str(answer_type or "").lower()
    return (
        "multiple" in normalized
        or normalized in {"mcq", "choice", "multiple_choice"}
    )
