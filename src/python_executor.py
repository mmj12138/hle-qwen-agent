from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class PythonExecutionResult:
    ok: bool
    stdout: str
    stderr: str
    returncode: Optional[int]
    error: str = ""


_ALLOWED_IMPORTS = {
    "math",
    "cmath",
    "itertools",
    "functools",
    "collections",
    "fractions",
    "decimal",
    "statistics",
    "heapq",
    "bisect",
    "random",
    "re",
}

_FORBIDDEN_CALLS = {
    "eval",
    "exec",
    "compile",
    "open",
    "input",
    "__import__",
    "globals",
    "locals",
    "vars",
    "dir",
    "getattr",
    "setattr",
    "delattr",
    "breakpoint",
    "help",
    "exit",
    "quit",
}

_FORBIDDEN_NODES = (
    ast.ClassDef,
    ast.AsyncFunctionDef,
    ast.Await,
    ast.AsyncFor,
    ast.AsyncWith,
    ast.With,
    ast.Global,
    ast.Nonlocal,
    ast.Yield,
    ast.YieldFrom,
)


class PythonExecutor:
    """Execute model-generated numerical Python in an isolated subprocess.

    This is a defensive execution environment, not a perfect security sandbox.
    It is appropriate for trusted benchmark-generated code on an HPC node, but
    should not be exposed to arbitrary hostile users.
    """

    def __init__(
        self,
        timeout_seconds: int = 5,
        memory_limit_mb: int = 1024,
        cpu_limit_seconds: int = 4,
        max_code_chars: int = 12000,
        max_output_chars: int = 16000,
    ):
        self.timeout_seconds = timeout_seconds
        self.memory_limit_mb = memory_limit_mb
        self.cpu_limit_seconds = cpu_limit_seconds
        self.max_code_chars = max_code_chars
        self.max_output_chars = max_output_chars

    def run(self, code: str) -> PythonExecutionResult:
        code = str(code or "").strip()

        if not code:
            return PythonExecutionResult(
                ok=False,
                stdout="",
                stderr="",
                returncode=None,
                error="empty_code",
            )

        if len(code) > self.max_code_chars:
            return PythonExecutionResult(
                ok=False,
                stdout="",
                stderr="",
                returncode=None,
                error="code_too_long",
            )

        validation_error = self._validate_ast(code)
        if validation_error:
            return PythonExecutionResult(
                ok=False,
                stdout="",
                stderr="",
                returncode=None,
                error=validation_error,
            )

        wrapper = (
            "# Auto-generated restricted benchmark computation\n"
            + code
            + "\n"
        )

        with tempfile.TemporaryDirectory(prefix="hle_python_tool_") as tmp:
            script_path = Path(tmp) / "solution.py"
            script_path.write_text(wrapper, encoding="utf-8")

            try:
                completed = subprocess.run(
                    [sys.executable, "-I", "-S", str(script_path)],
                    cwd=tmp,
                    env={
                        "PATH": os.environ.get("PATH", ""),
                        "PYTHONIOENCODING": "utf-8",
                    },
                    text=True,
                    capture_output=True,
                    timeout=self.timeout_seconds,
                    preexec_fn=self._resource_limiter()
                    if os.name == "posix"
                    else None,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                return PythonExecutionResult(
                    ok=False,
                    stdout=(exc.stdout or "")[: self.max_output_chars],
                    stderr=(exc.stderr or "")[: self.max_output_chars],
                    returncode=None,
                    error="timeout",
                )
            except Exception as exc:
                return PythonExecutionResult(
                    ok=False,
                    stdout="",
                    stderr="",
                    returncode=None,
                    error=f"execution_error:{type(exc).__name__}:{exc}",
                )

        stdout = completed.stdout[: self.max_output_chars]
        stderr = completed.stderr[: self.max_output_chars]

        return PythonExecutionResult(
            ok=completed.returncode == 0,
            stdout=stdout,
            stderr=stderr,
            returncode=completed.returncode,
            error="" if completed.returncode == 0 else "nonzero_exit",
        )

    def _validate_ast(self, code: str) -> str:
        try:
            tree = ast.parse(code, mode="exec")
        except SyntaxError as exc:
            return f"syntax_error:{exc.msg}"

        for node in ast.walk(tree):
            if isinstance(node, _FORBIDDEN_NODES):
                return f"forbidden_node:{type(node).__name__}"

            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".", 1)[0]
                    if root not in _ALLOWED_IMPORTS:
                        return f"forbidden_import:{alias.name}"

            if isinstance(node, ast.ImportFrom):
                module = (node.module or "").split(".", 1)[0]
                if module not in _ALLOWED_IMPORTS:
                    return f"forbidden_import:{node.module}"

            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in _FORBIDDEN_CALLS:
                        return f"forbidden_call:{node.func.id}"

                if isinstance(node.func, ast.Attribute):
                    if node.func.attr.startswith("_"):
                        return f"forbidden_attribute:{node.func.attr}"

            if isinstance(node, ast.Attribute) and node.attr.startswith("_"):
                return f"forbidden_attribute:{node.attr}"

            if isinstance(node, ast.Name) and node.id.startswith("__"):
                return f"forbidden_name:{node.id}"

        if "FINAL_ANSWER:" not in code:
            return "missing_final_answer_print"

        return ""

    def _resource_limiter(self):
        memory_bytes = self.memory_limit_mb * 1024 * 1024
        cpu_seconds = self.cpu_limit_seconds

        def limit_resources() -> None:
            try:
                import resource

                resource.setrlimit(
                    resource.RLIMIT_CPU,
                    (cpu_seconds, cpu_seconds),
                )
                resource.setrlimit(
                    resource.RLIMIT_AS,
                    (memory_bytes, memory_bytes),
                )
                resource.setrlimit(
                    resource.RLIMIT_FSIZE,
                    (0, 0),
                )
                resource.setrlimit(
                    resource.RLIMIT_NOFILE,
                    (16, 16),
                )
                resource.setrlimit(
                    resource.RLIMIT_NPROC,
                    (0, 0),
                )
            except Exception:
                # The outer timeout and AST checks still apply.
                pass

        return limit_resources


def extract_python_final_answer(stdout: str) -> str:
    matches = re.findall(
        r"(?im)^\s*FINAL_ANSWER\s*:\s*(.*?)\s*$",
        str(stdout or ""),
    )
    if not matches:
        return ""
    return matches[-1].strip()
