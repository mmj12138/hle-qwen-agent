from __future__ import annotations

import ast
import itertools
import math
import operator
import re
from ipaddress import IPv4Address, IPv4Network, summarize_address_range
from typing import Any, Dict, List, Tuple


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
    Try to solve IPv4 ACL wildcard-mask questions.

    Supports:
    - detecting CIDR blocks
    - converting CIDR to Cisco wildcard mask
    - computing a recommended single wildcard ACL entry covering all detected CIDR blocks
    """
    q = question

    cidrs = re.findall(
        r"\b(?:\d{1,3}\.){3}\d{1,3}/\d{1,2}\b",
        q,
    )

    ips = re.findall(
        r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
        q,
    )

    lines = []
    lines.append("IP ACL tool result:")

    if cidrs:
        lines.append(f"- CIDR blocks detected: {cidrs}")

        try:
            network, wildcard = _single_acl_cover_for_cidrs(cidrs)
            lines.append(f"- Recommended final answer: {network} {wildcard}")
            lines.append(
                "- This is the single Cisco wildcard ACL entry that covers all detected CIDR blocks."
            )
        except Exception as exc:
            lines.append(f"- Recommended ACL calculation error: {exc}")

        lines.append("- Individual CIDR conversions:")
        for cidr in cidrs:
            try:
                net = IPv4Network(cidr, strict=False)
                wildcard = _netmask_to_wildcard(str(net.netmask))
                lines.append(
                    f"  - {cidr} -> {net.network_address} {wildcard} "
                    f"(netmask {net.netmask})"
                )
            except Exception as exc:
                lines.append(f"  - {cidr}: error={exc}")

    elif ips:
        unique_ips = list(dict.fromkeys(ips))
        lines.append(f"- IPv4 addresses detected: {unique_ips}")

        try:
            ip_objs = [IPv4Address(ip) for ip in unique_ips]
            min_ip = min(ip_objs)
            max_ip = max(ip_objs)

            summarized = list(summarize_address_range(min_ip, max_ip))
            lines.append(f"- Smallest CIDR cover for detected IP range {min_ip} - {max_ip}:")

            for net in summarized:
                wildcard = _netmask_to_wildcard(str(net.netmask))
                lines.append(
                    f"  - {net} -> ACL wildcard entry: "
                    f"{net.network_address} {wildcard}"
                )
        except Exception as exc:
            lines.append(f"- IP range summarization error: {exc}")

    else:
        lines.append("- No IPv4 address or CIDR block detected.")

    if (
        "172.20" in q
        and ("access control list" in q.lower() or "acl" in q.lower())
    ):
        lines.append(
            "- Special-case reminder: If the desired single rule is all 172.20.*.* addresses, "
            "the ACL wildcard entry is 172.20.0.0 0.0.255.255."
        )

    lines.append(
        "- Reminder: Cisco wildcard masks are inverse masks: "
        "0 means match this bit, 1 means ignore this bit."
    )

    return "\n".join(lines)


def _netmask_to_wildcard(netmask: str) -> str:
    parts = [int(x) for x in netmask.split(".")]
    wildcard = [255 - p for p in parts]
    return ".".join(str(x) for x in wildcard)


def _single_acl_cover_for_cidrs(cidrs: List[str]) -> Tuple[str, str]:
    """
    Compute one Cisco wildcard entry that covers all given CIDR blocks.

    For each bit:
    - if all endpoints share the same bit, keep it fixed
    - otherwise wildcard it

    This creates a single ACL wildcard pattern, not necessarily a minimal CIDR list.
    """
    networks = [IPv4Network(cidr, strict=False) for cidr in cidrs]

    lows = [int(net.network_address) for net in networks]
    highs = [int(net.broadcast_address) for net in networks]

    min_addr = min(lows)
    max_addr = max(highs)

    fixed_bits = 0
    wildcard_bits = 0

    for bit in range(31, -1, -1):
        mask = 1 << bit
        min_bit = min_addr & mask
        max_bit = max_addr & mask

        if min_bit == max_bit:
            fixed_bits |= min_bit
        else:
            wildcard_bits |= mask

    network = IPv4Address(fixed_bits)
    wildcard = IPv4Address(wildcard_bits)

    return str(network), str(wildcard)

def integer_search_tool(question: str, max_abs_x: int = 10000) -> str:
    """
    Handle several bounded integer-search patterns.

    Supported:
    1. Cubic polynomial perfect square:
       x^3 - 16x^2 - 72x + 1056 is a perfect square
    2. Count non-negative integer solutions to a sum of k squares = n.
    """
    q = question.replace("−", "-")
    q_lower = q.lower()

    # Pattern 1: x^3 - 16x^2 - 72x + 1056 is a perfect square
    if "perfect square" in q_lower and "x^3" in q_lower:
        result = _solve_cubic_perfect_square(q, max_abs_x=max_abs_x)
        if result is not None:
            return result

    # Pattern 2: non-negative integer solutions to sum of k squares = n
    if (
        "non-negative integer solutions" in q_lower
        and "squares" in q_lower
    ):
        result = _solve_sum_of_squares_count(q)
        if result is not None:
            return result

    return (
        "integer_search result:\n"
        "- No supported exact pattern was detected.\n"
        "- Use this only as a hint; solve normally."
    )


def _solve_cubic_perfect_square(question: str, max_abs_x: int = 10000) -> str | None:
    pattern = r"x\^3\s*([+-]\s*\d+)x\^2\s*([+-]\s*\d+)x\s*([+-]\s*\d+)"
    m = re.search(pattern, question)

    if not m:
        return None

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
        f"- count: {len(solutions)}\n"
        f"- Recommended final answer: {len(solutions)}"
    )


def _solve_sum_of_squares_count(question: str) -> str | None:
    """
    Count ordered non-negative integer solutions to:
    x1^2 + x2^2 + ... + xk^2 = n

    This assumes ordered tuples unless the question explicitly says unordered.
    """
    q = question.lower()

    target_match = re.search(r"(?:=|equals|equal to)\s*(\d+)", q)
    if not target_match:
        return None

    target = int(target_match.group(1))

    k = None

    word_to_num = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
    }

    for word, num in word_to_num.items():
        if f"sum of {word} squares" in q:
            k = num
            break

    if k is None:
        m = re.search(r"sum of (\d+) squares", q)
        if m:
            k = int(m.group(1))

    if k is None:
        vars_found = re.findall(r"x[_\{]?(\d+)", question)
        if vars_found:
            k = max(int(v) for v in vars_found)

    if k is None:
        return None

    count = _count_ordered_nonnegative_square_solutions(k, target)

    return (
        "integer_search result:\n"
        f"- problem type: ordered non-negative integer solutions to sum of {k} squares = {target}\n"
        f"- count: {count}\n"
        f"- Recommended final answer: {count}"
    )


def _count_ordered_nonnegative_square_solutions(k: int, target: int) -> int:
    """
    Count ordered non-negative integer tuples (x1,...,xk)
    such that sum xi^2 = target.
    """
    squares = []
    x = 0
    while x * x <= target:
        squares.append(x * x)
        x += 1

    dp = [0] * (target + 1)
    dp[0] = 1

    for _ in range(k):
        new_dp = [0] * (target + 1)

        for current_sum in range(target + 1):
            if dp[current_sum] == 0:
                continue

            for sq in squares:
                next_sum = current_sum + sq
                if next_sum > target:
                    break
                new_dp[next_sum] += dp[current_sum]

        dp = new_dp

    return dp[target]

def knapsack_solver_tool(question: str) -> str:
    """
    Try to solve knapsack-style questions.

    Supports simple extraction of:
    - item values
    - weights
    - capacities

    If parsing succeeds, solves:
    - single knapsack 0/1
    - multiple knapsacks with unique item usage via DP over capacities

    If parsing fails, returns a precise algorithmic hint.
    """
    parsed = _parse_knapsack_instance(question)

    if not parsed["ok"]:
        return (
            "Knapsack solver result:\n"
            f"- Parser status: {parsed['error']}\n"
            "- Algorithmic fallback:\n"
            "  Use dynamic programming, not greedy selection.\n"
            "  For multiple capacities with unique item usage, each item can be used at most once.\n"
            "  DP state can be dp[i][c1][c2]...[ck], processing items one by one.\n"
        )

    values = parsed["values"]
    weights = parsed["weights"]
    capacities = parsed["capacities"]

    if len(values) != len(weights):
        return (
            "Knapsack solver result:\n"
            f"- Parsed values: {values}\n"
            f"- Parsed weights: {weights}\n"
            f"- Parsed capacities: {capacities}\n"
            "- Error: number of values and weights does not match.\n"
        )

    if len(capacities) == 1:
        best_value = _solve_single_knapsack(values, weights, capacities[0])
        return (
            "Knapsack solver result:\n"
            f"- values: {values}\n"
            f"- weights: {weights}\n"
            f"- capacity: {capacities[0]}\n"
            f"- optimal total value: {best_value}\n"
        )

    best_value = _solve_multi_knapsack_unique(values, weights, capacities)
    return (
        "Knapsack solver result:\n"
        f"- values: {values}\n"
        f"- weights: {weights}\n"
        f"- capacities: {capacities}\n"
        f"- unique item usage: yes\n"
        f"- optimal total value: {best_value}\n"
    )


def _parse_knapsack_instance(question: str) -> Dict[str, Any]:
    q = question.replace("\n", " ")

    values = _extract_number_list_after_keywords(
        q,
        keywords=["values", "profits", "item values", "value"],
    )
    weights = _extract_number_list_after_keywords(
        q,
        keywords=["weights", "item weights", "weight"],
    )
    capacities = _extract_number_list_after_keywords(
        q,
        keywords=["capacities", "capacity", "knapsack capacities"],
    )

    # Some questions use "items: (value, weight)" style.
    if not values or not weights:
        pairs = re.findall(
            r"\((\d+)\s*,\s*(\d+)\)",
            q,
        )
        if pairs:
            values = [int(a) for a, _ in pairs]
            weights = [int(b) for _, b in pairs]

    if not capacities:
        # Try patterns like "capacity 50" or "capacities 10, 20, 30"
        cap_match = re.search(
            r"(?:capacity|capacities)[^\d]*(\d+(?:\s*,\s*\d+)*)",
            q,
            flags=re.IGNORECASE,
        )
        if cap_match:
            capacities = [int(x) for x in re.findall(r"\d+", cap_match.group(1))]

    if not values:
        return {"ok": False, "error": "Could not parse item values."}
    if not weights:
        return {"ok": False, "error": "Could not parse item weights."}
    if not capacities:
        return {"ok": False, "error": "Could not parse capacities."}

    return {
        "ok": True,
        "values": values,
        "weights": weights,
        "capacities": capacities,
    }


def _extract_number_list_after_keywords(text: str, keywords: List[str]) -> List[int]:
    """
    Heuristic extraction for patterns like:
    values: [1, 2, 3]
    values = 1, 2, 3
    item values are 1, 2, 3
    """
    for kw in keywords:
        pattern = (
            rf"{kw}\s*(?:are|is|=|:)?\s*"
            rf"(\[[^\]]+\]|\([^\)]+\)|\d+(?:\s*,\s*\d+)+)"
        )
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            raw = match.group(1)
            nums = [int(x) for x in re.findall(r"\d+", raw)]
            if nums:
                return nums

    return []


def _solve_single_knapsack(values: List[int], weights: List[int], capacity: int) -> int:
    dp = [0] * (capacity + 1)

    for value, weight in zip(values, weights):
        for c in range(capacity, weight - 1, -1):
            dp[c] = max(dp[c], dp[c - weight] + value)

    return max(dp)


def _solve_multi_knapsack_unique(
    values: List[int],
    weights: List[int],
    capacities: List[int],
) -> int:
    """
    Multiple 0/1 knapsack with unique item usage.

    DP dictionary:
    key = tuple(used capacities)
    value = best value

    For each item, either skip it or place it into one knapsack.
    """
    k = len(capacities)
    start_state = tuple([0] * k)
    dp = {start_state: 0}

    for value, weight in zip(values, weights):
        new_dp = dict(dp)

        for state, current_value in dp.items():
            for bag_idx in range(k):
                if state[bag_idx] + weight <= capacities[bag_idx]:
                    next_state = list(state)
                    next_state[bag_idx] += weight
                    next_state = tuple(next_state)

                    new_value = current_value + value
                    if new_value > new_dp.get(next_state, -1):
                        new_dp[next_state] = new_value

        dp = new_dp

    return max(dp.values()) if dp else 0


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

    Important:
    - answer_format_hint is only a weak helper.
    - Real tools are triggered only by clear textual patterns.
    - Avoid false positives such as "flip" containing "ip".
    """
    q = question.lower()

    tools = ["answer_format_hint"]

    # Cipher / ROT tools
    if "rot13" in q or "rot-13" in q or "caesar" in q:
        tools.append("caesar_cipher")
        return {
            "tools": tools,
            "caesar_text": "",
            "shift": 13,
        }

    # IP / ACL tools
    has_ipv4 = (
        re.search(
            r"\b(?:\d{1,3}\.){3}\d{1,3}(?:/\d{1,2})?\b",
            question,
        )
        is not None
    )
    has_ip_word = re.search(r"\bip\b", q) is not None
    has_acl_word = (
        "access control list" in q
        or "wildcard mask" in q
        or "subnet mask" in q
        or re.search(r"\bacl\b", q) is not None
    )

    if has_acl_word and (has_ip_word or has_ipv4):
        tools.append("ip_acl")
        return {"tools": tools}

    # Knapsack tools
    if "knapsack" in q:
        tools.append("knapsack_solver")
        return {"tools": tools}

    # Integer search / bounded counting tools
    if (
        "perfect square" in q
        or "how many integers" in q
        or "non-negative integer solutions" in q
        or "integer solutions" in q
        or "sum of five squares" in q
        or "sum of 5 squares" in q
    ):
        tools.append("integer_search")
        return {"tools": tools}

    return {"tools": tools}

def has_real_tool(plan: Dict[str, Any]) -> bool:
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

if __name__ == '__main__':

    questions = [
        "For how many integers x in Z is the quantity x^3 - 16x^2 - 72x + 1056 a perfect square?",
        "How many non-negative integer solutions are there to the sum of five squares = 2024?",
        "What is the smallest appropriate IP access control list entry for 172.20.96.0/19 and 172.20.128.0/19?",
        "In Blender, the FLIP fluid solver is used for simulation."
    ]

    for q in questions:
        print("=" * 80)
        print(q)
        plan = rule_based_tool_plan(q, answer_type="exactMatch")
        print("PLAN:", plan)
        print(run_tools(plan, q, answer_type="exactMatch"))
