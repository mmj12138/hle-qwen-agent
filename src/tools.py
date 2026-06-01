from __future__ import annotations

import ast
import json
import math
import operator
import re
from typing import Any, Dict


_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.Mod: operator.mod,
}


def safe_calculator(expression: str) -> str:
    try:
        tree = ast.parse(expression, mode="eval")
        value = _eval_ast(tree.body)
        return str(value)
    except Exception as exc:
        return f"calculator_error: {exc}"


def _eval_ast(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value

    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](
            _eval_ast(node.left),
            _eval_ast(node.right),
        )

    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](_eval_ast(node.operand))

    raise ValueError(f"Unsupported expression node: {type(node).__name__}")


def caesar_cipher_tool(text: str, shift: int = 13) -> str:
    result = []

    for ch in text:
        if "a" <= ch <= "z":
            base = ord("a")
            result.append(chr((ord(ch) - base + shift) % 26 + base))
        elif "A" <= ch <= "Z":
            base = ord("A")
            result.append(chr((ord(ch) - base + shift) % 26 + base))
        else:
            result.append(ch)

    return "".join(result)


def ip_acl_tool(question: str) -> str:
    """
    Lightweight IP ACL helper.

    It is designed for questions involving IPv4 ACL wildcard masks.
    It does not fully solve every networking question, but it provides
    stable reminders about Cisco wildcard-mask format.
    """
    ips = re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", question)

    return (
        "IP ACL helper:\n"
        "- Cisco ACL wildcard masks are inverse masks.\n"
        "- 0 means the bit must match; 255 means any value is allowed.\n"
        "- Example: 172.20.0.0 0.0.255.255 covers 172.20.*.*.\n"
        f"- IPv4-like strings detected in the question: {ips}"
    )


def integer_search_tool(question: str, max_abs_x: int = 10000) -> str:
    """
    Handle a few bounded integer-search patterns.
    Especially useful for perfect-square polynomial questions.
    """
    q = question

    # Pattern: x^3 - 16x^2 - 72x + 1056 is a perfect square
    if "perfect square" in q.lower() and "x^3" in q.lower():
        expr = q.replace("−", "-")
        pattern = r"x\^3\s*([+-]\s*\d+)x\^2\s*([+-]\s*\d+)x\s*([+-]\s*\d+)"
        m = re.search(pattern, expr)

        if m:
            a = int(m.group(1).replace(" ", ""))
            b = int(m.group(2).replace(" ", ""))
            c = int(m.group(3).replace(" ", ""))

            solutions = []
            for x in range(-max_abs_x, max_abs_x + 1):
                value = x**3 + a * x**2 + b * x + c
                if value >= 0:
                    r = math.isqrt(value)
                    if r * r == value:
                        solutions.append(x)

            return (
                "integer_search result:\n"
                f"- expression: x^3 {a:+d}x^2 {b:+d}x {c:+d}\n"
                f"- integer x values in [-{max_abs_x}, {max_abs_x}] making it a perfect square: {solutions}\n"
                f"- count: {len(solutions)}"
            )

    return (
        "integer_search result:\n"
        "- No supported exact pattern was detected.\n"
        "- Use this only as a hint; solve normally."
    )


def knapsack_solver_tool(question: str) -> str:
    """
    Placeholder helper for knapsack-style questions.

    Full parsing of arbitrary natural-language knapsack instances is hard.
    This tool gives the solver a reliable algorithmic plan instead of guessing.
    """
    return (
        "Knapsack solver hint:\n"
        "- This is a combinatorial optimization problem.\n"
        "- Use dynamic programming over capacities and item index.\n"
        "- For multiple capacities with unique item usage, each item can be assigned to at most one knapsack.\n"
        "- Do not greedily choose by value or value/weight unless the instance is fractional knapsack."
    )


def answer_format_hint(answer_type: str) -> str:
    answer_type = (answer_type or "").lower()

    if "multiple" in answer_type or "choice" in answer_type:
        return "Return only one option letter, such as A, B, C, D, or E."

    if "exact" in answer_type:
        return "Return only the exact concise answer. Do not include explanation."

    return "Return only the final answer in the requested format."


def rule_based_tool_plan(question: str, answer_type: str = "") -> Dict[str, Any]:
    """
    Deterministic tool planner.

    Important design:
    - answer_format_hint is a weak helper, not a real problem-solving tool.
    - Real tools are only triggered when the question explicitly matches.
    """
    q = question.lower()

    tools = ["answer_format_hint"]

    if "rot13" in q or "rot-13" in q:
        tools.append("caesar_cipher")
        return {
            "tools": tools,
            "caesar_text": "",
            "shift": 13,
        }

    if (
        "access control list" in q
        or "wildcard mask" in q
        or "acl" in q
    ) and "ip" in q:
        tools.append("ip_acl")
        return {
            "tools": tools,
        }

    if "knapsack" in q:
        tools.append("knapsack_solver")
        return {
            "tools": tools,
        }

    if (
        "perfect square" in q
        or "how many integers" in q
        or "non-negative integer solutions" in q
        or "integer solutions" in q
    ):
        tools.append("integer_search")
        return {
            "tools": tools,
        }

    return {
        "tools": tools,
    }


def has_real_tool(plan: Dict[str, Any]) -> bool:
    """
    Real tools provide problem-specific evidence.
    answer_format_hint alone is not a real tool.
    """
    tools = plan.get("tools", [])
    if isinstance(tools, str):
        tools = [tools]

    real_tools = {
        "calculator",
        "caesar_cipher",
        "ip_acl",
        "integer_search",
        "knapsack_solver",
    }

    return any(t in real_tools for t in tools)


def run_tools(plan: Dict[str, Any], question: str, answer_type: str = "") -> Dict[str, Any]:
    results: Dict[str, Any] = {}

    tools = plan.get("tools", [])
    if isinstance(tools, str):
        tools = [tools]

    if "answer_format_hint" in tools:
        results["answer_format_hint"] = answer_format_hint(answer_type)

    if "calculator" in tools:
        expr = plan.get("calculator_expression", "")
        results["calculator"] = {
            "expression": expr,
            "result": safe_calculator(expr) if expr else "no expression provided",
        }

    if "caesar_cipher" in tools:
        text = plan.get("caesar_text", "")
        shift = int(plan.get("shift", 13))
        results["caesar_cipher"] = {
            "input": text,
            "shift": shift,
            "result": caesar_cipher_tool(text, shift) if text else "no text provided",
        }

    if "ip_acl" in tools:
        results["ip_acl"] = ip_acl_tool(question)

    if "integer_search" in tools:
        results["integer_search"] = integer_search_tool(question)

    if "knapsack_solver" in tools:
        results["knapsack_solver"] = knapsack_solver_tool(question)

    return results