"""
Expert Task: Calculator Safety + Advanced Math Conflict

Two developers extend a basic Calculator class:
  - Branch 'refactor-safety': Adds ZeroDivisionError handling to divide(),
    type hints (Union[int, float]) across all methods, and a safety demo in main.py.
  - Branch 'feature-advanced': Adds 'import math' and three new methods —
    power(), sqrt(), absolute() — and an advanced demo function in main.py.

Both branches modify the same sections in both files, producing conflicts in:
  - The module-level import block of calculator.py
  - The divide() method body of calculator.py
  - The run_demo() function body of main.py

The expert-level tests require BOTH branches to be merged correctly:
  - test_divide_raises_zero_division only passes with Branch A's guard
  - test_power_functional and test_sqrt_functional only pass with Branch B's methods
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

# ── Base versions ──────────────────────────────────────────────────────────────

BASE_CALCULATOR = '''\
"""Calculator module."""


class Calculator:
    """Basic arithmetic calculator."""

    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b

    def multiply(self, a, b):
        return a * b

    def divide(self, a, b):
        return a / b
'''

BASE_MAIN = '''\
"""Calculator demo."""

from calculator import Calculator


def run_demo():
    """Demonstrate basic calculator operations."""
    calc = Calculator()
    print(f"2 + 3 = {calc.add(2, 3)}")
    print(f"10 - 4 = {calc.subtract(10, 4)}")
    print(f"3 * 7 = {calc.multiply(3, 7)}")
    print(f"15 / 3 = {calc.divide(15, 3)}")


if __name__ == "__main__":
    run_demo()
'''

# ── Branch A: refactor-safety ─────────────────────────────────────────────────

BRANCH_A_CALCULATOR = '''\
"""Calculator module."""

from typing import Union

Number = Union[int, float]


class Calculator:
    """Basic arithmetic calculator."""

    def add(self, a: Number, b: Number) -> Number:
        return a + b

    def subtract(self, a: Number, b: Number) -> Number:
        return a - b

    def multiply(self, a: Number, b: Number) -> Number:
        return a * b

    def divide(self, a: Number, b: Number) -> float:
        if b == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        return float(a) / float(b)
'''

BRANCH_A_MAIN = '''\
"""Calculator demo."""

from calculator import Calculator


def run_demo():
    """Demonstrate basic and safe calculator operations."""
    calc = Calculator()
    print(f"2 + 3 = {calc.add(2, 3)}")
    print(f"10 - 4 = {calc.subtract(10, 4)}")
    print(f"3 * 7 = {calc.multiply(3, 7)}")
    print(f"15 / 3 = {calc.divide(15, 3)}")
    try:
        calc.divide(1, 0)
    except ZeroDivisionError as exc:
        print(f"Safe: {exc}")


if __name__ == "__main__":
    run_demo()
'''

# ── Branch B: feature-advanced ────────────────────────────────────────────────

BRANCH_B_CALCULATOR = '''\
"""Calculator module."""

import math


class Calculator:
    """Basic arithmetic calculator."""

    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b

    def multiply(self, a, b):
        return a * b

    def divide(self, a, b):
        """Divide a by b, returning a float."""
        return a / b

    def power(self, base, exp):
        """Raise base to the power of exp."""
        return math.pow(base, exp)

    def sqrt(self, n):
        """Return the square root of n."""
        if n < 0:
            raise ValueError("Cannot take sqrt of a negative number")
        return math.sqrt(n)

    def absolute(self, n):
        """Return the absolute value of n."""
        return abs(n)
'''

BRANCH_B_MAIN = '''\
"""Calculator demo."""

from calculator import Calculator


def run_demo():
    """Demonstrate basic calculator operations."""
    calc = Calculator()
    print("=== Basic Operations ===")
    print(f"2 + 3 = {calc.add(2, 3)}")
    print(f"10 - 4 = {calc.subtract(10, 4)}")
    print(f"3 * 7 = {calc.multiply(3, 7)}")
    print(f"15 / 3 = {calc.divide(15, 3)}")


def run_advanced_demo():
    """Demonstrate advanced math operations."""
    calc = Calculator()
    print("=== Advanced Operations ===")
    print(f"2^10 = {calc.power(2, 10)}")
    print(f"sqrt(16) = {calc.sqrt(16)}")
    print(f"|-5| = {calc.absolute(-5)}")


if __name__ == "__main__":
    run_demo()
    run_advanced_demo()
'''


def setup_task(workspace_dir: str) -> None:
    """Create the conflicted git repo in workspace_dir."""
    ws = Path(workspace_dir)
    ws.mkdir(parents=True, exist_ok=True)

    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Dev",
        "GIT_AUTHOR_EMAIL": "dev@test.com",
        "GIT_COMMITTER_NAME": "Dev",
        "GIT_COMMITTER_EMAIL": "dev@test.com",
    }

    def run_git(*args: str) -> None:
        subprocess.run(
            ["git"] + list(args), cwd=str(ws),
            capture_output=True, text=True, check=True, env=env,
        )

    run_git("init")
    run_git("checkout", "-b", "main")

    (ws / "calculator.py").write_text(BASE_CALCULATOR, encoding="utf-8")
    (ws / "main.py").write_text(BASE_MAIN, encoding="utf-8")
    run_git("add", ".")
    run_git("commit", "-m", "Initial commit: basic Calculator class and demo")

    # Branch A: add type safety and ZeroDivisionError guard
    run_git("checkout", "-b", "refactor-safety")
    (ws / "calculator.py").write_text(BRANCH_A_CALCULATOR, encoding="utf-8")
    (ws / "main.py").write_text(BRANCH_A_MAIN, encoding="utf-8")
    run_git("add", ".")
    run_git("commit", "-m", "Refactor: add type hints and safe divide with ZeroDivisionError")

    # Branch B: add power, sqrt, absolute and advanced demo
    run_git("checkout", "main")
    run_git("checkout", "-b", "feature-advanced")
    (ws / "calculator.py").write_text(BRANCH_B_CALCULATOR, encoding="utf-8")
    (ws / "main.py").write_text(BRANCH_B_MAIN, encoding="utf-8")
    run_git("add", ".")
    run_git("commit", "-m", "Feature: add power, sqrt, absolute methods and advanced demo")

    # Merge feature-advanced into refactor-safety → produces conflicts
    run_git("checkout", "refactor-safety")
    subprocess.run(
        ["git", "merge", "feature-advanced", "--no-edit"],
        cwd=str(ws), capture_output=True, text=True, env=env,
    )


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        setup_task(tmp)
        for f in ["calculator.py", "main.py"]:
            p = Path(tmp) / f
            if p.exists():
                print(f"=== {f} ===")
                print(p.read_text(encoding="utf-8"))
                print()
