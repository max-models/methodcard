"""Orders of convergence and SymPy rules."""

import pytest
import sympy

from methodcard import ConvergenceProblem, Rule, observed_order
from methodcard.checks import check_order, check_rule

x, y = sympy.symbols("x y")


def test_observed_order():
    steps = [0.1, 0.05, 0.025]
    assert observed_order(steps, [3 * h**2 for h in steps]) == pytest.approx(2.0)
    with pytest.raises(ValueError, match="at least two"):
        observed_order([0.1], [0.1])
    with pytest.raises(ValueError, match="positive"):
        observed_order([0.1, 0.05], [0.0, 1.0])


def test_check_order_single_and_per_variable():
    first = ConvergenceProblem(lambda h: h, steps=(0.1, 0.05))
    assert check_order(first, 1) == {"order": pytest.approx(1.0)}
    both = ConvergenceProblem(lambda h: {"x": h**2, "v": h}, steps=(0.1, 0.05))
    assert check_order(both, {"x": 2, "v": 1}) == {
        "x": pytest.approx(2),
        "v": pytest.approx(1),
    }
    with pytest.raises(AssertionError, match="v: observed order 1.000, declared 2"):
        check_order(both, {"x": 2, "v": 2})


def test_check_order_tolerance():
    loose = ConvergenceProblem(lambda h: h**1.3, steps=(0.1, 0.05), tolerance=0.5)
    check_order(loose, 1)
    with pytest.raises(AssertionError):
        check_order(ConvergenceProblem(lambda h: h**1.3, steps=(0.1, 0.05)), 1)


def test_check_rule():
    check_rule(x * y, lambda x, y: x * y)
    check_rule(Rule(x - y, ranges={"x": (5, 6)}), lambda x, y: x - y)
    check_rule(Rule(x**2, implementation=lambda x: x * x), None)
    check_rule(sympy.Integer(3), lambda: 3.0)
    check_rule(sympy.erf(x), lambda x: __import__("math").erf(x))
    with pytest.raises(AssertionError):
        check_rule(x * y, lambda x, y: x * y * (1 + 1e-6))
    with pytest.raises(TypeError, match="needs Rule"):
        check_rule(x, None)
    with pytest.raises(TypeError, match="needs Rule"):
        check_rule(x, int)
