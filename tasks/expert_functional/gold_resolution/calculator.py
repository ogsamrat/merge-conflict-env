"""Calculator module."""

import math
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
        """Divide a by b, returning a float."""
        if b == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        return float(a) / float(b)

    def power(self, base: Number, exp: Number) -> float:
        """Raise base to the power of exp."""
        return math.pow(base, exp)

    def sqrt(self, n: Number) -> float:
        """Return the square root of n."""
        if n < 0:
            raise ValueError("Cannot take sqrt of a negative number")
        return math.sqrt(n)

    def absolute(self, n: Number) -> Number:
        """Return the absolute value of n."""
        return abs(n)
