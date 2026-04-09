"""Calculator demo."""

from calculator import Calculator


def run_demo():
    """Demonstrate basic and safe calculator operations."""
    calc = Calculator()
    print("=== Basic Operations ===")
    print(f"2 + 3 = {calc.add(2, 3)}")
    print(f"10 - 4 = {calc.subtract(10, 4)}")
    print(f"3 * 7 = {calc.multiply(3, 7)}")
    print(f"15 / 3 = {calc.divide(15, 3)}")
    try:
        calc.divide(1, 0)
    except ZeroDivisionError as exc:
        print(f"Safe: {exc}")


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
