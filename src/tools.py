from __future__ import annotations

import ast
import operator
import codecs
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
    """
    A small safe arithmetic calculator.
    It intentionally supports only simple numeric expressions.
    """
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
        return _ALLOWED_OPERATORS[type(node.op)](_eval_ast(node.left), _eval_ast(node.right))

    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](_eval_ast(node.operand))

    raise ValueError(f"Unsupported expression node: {type(node).__name__}")


def rot13_tool(text: str) -> str:
    """
    Apply ROT13 to a string.
    Useful for puzzle-style HLE questions.
    """
    try:
        return codecs.decode(text, "rot_13")
    except Exception as exc:
        return f"rot13_error: {exc}"


def mass_compare_tool(body_a: str, body_b: str, target: str) -> str:
    """
    Compare which body is closer in mass to a target body.

    This is intentionally tiny and deterministic. It is useful for
    simple astronomy comparison questions, not general physics.
    """
    masses = {
        "moon": 7.342e22,
        "earth": 5.972e24,
        "mars": 6.417e23,
        "venus": 4.867e24,
        "mercury": 3.301e23,
        "jupiter": 1.898e27,
        "saturn": 5.683e26,
        "uranus": 8.681e25,
        "neptune": 1.024e26,
        "sun": 1.989e30,
    }

    a = body_a.lower().strip()
    b = body_b.lower().strip()
    t = target.lower().strip()

    if a not in masses or b not in masses or t not in masses:
        return "mass_compare_error: unknown body"

    da = abs(masses[t] - masses[a])
    db = abs(masses[t] - masses[b])

    closer = body_a if da < db else body_b

    return (
        f"{target} mass = {masses[t]:.3e} kg; "
        f"{body_a} mass = {masses[a]:.3e} kg; "
        f"{body_b} mass = {masses[b]:.3e} kg; "
        f"{target} is closer in mass to {closer}."
    )


def answer_format_hint(answer_type: str) -> str:
    """
    Give deterministic formatting advice based on HLE answer type.
    """
    answer_type = (answer_type or "").lower()

    if "multiple" in answer_type or "choice" in answer_type:
        return "Return only one option letter, such as A, B, C, D, or E."

    if "exact" in answer_type:
        return "Return only the exact concise answer. Do not include explanation."

    return "Return only the final answer in the requested format."


def domain_hint(question: str) -> str:
    q = question.lower()

    if any(k in q for k in ["integral", "derivative", "matrix", "probability", "theorem", "bordism", "elliptic curve"]):
        return "math"
    if any(k in q for k in ["molecule", "reaction", "protein", "cell", "gene"]):
        return "science"
    if any(k in q for k in ["war", "empire", "century", "philosopher", "author", "arrhenius"]):
        return "humanities"
    if any(k in q for k in ["force", "energy", "quantum", "electron", "velocity", "mass", "mars", "moon", "earth"]):
        return "physics"

    return "unknown"


def run_tools(plan: Dict[str, Any], question: str, answer_type: str = "") -> Dict[str, Any]:
    results: Dict[str, Any] = {}

    tools = plan.get("tools", [])
    if isinstance(tools, str):
        tools = [tools]

    if "calculator" in tools:
        expr = plan.get("calculator_expression", "")
        results["calculator"] = {
            "expression": expr,
            "result": safe_calculator(expr) if expr else "no expression provided",
        }

    if "rot13" in tools:
        text = plan.get("rot13_text", "")
        results["rot13"] = {
            "input": text,
            "result": rot13_tool(text) if text else "no text provided",
        }

    if "mass_compare" in tools:
        body_a = plan.get("body_a", "Earth")
        body_b = plan.get("body_b", "Moon")
        target = plan.get("target", "Mars")
        results["mass_compare"] = {
            "body_a": body_a,
            "body_b": body_b,
            "target": target,
            "result": mass_compare_tool(body_a, body_b, target),
        }

    if "answer_format_hint" in tools:
        results["answer_format_hint"] = answer_format_hint(answer_type)

    if "domain_hint" in tools:
        results["domain_hint"] = domain_hint(question)

    if not results:
        results["no_tool"] = "No external tool result. Use model reasoning only."

    return results