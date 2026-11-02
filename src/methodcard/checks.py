"""The checks behind the generated tests: SymPy rules and orders of convergence."""

from __future__ import annotations

import inspect
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass(frozen=True)
class Rule:
    """A SymPy rule checked against the implementation on random inputs.

    The implementation is called with keyword arguments named after the rule's free
    symbols. A bare SymPy expression in ``symbolic`` stands for ``Rule(expr)``; on a
    function, its symbols are then named after the function's parameters.

    Attributes:
        expr: The SymPy expression.
        implementation: Called with the symbols as keywords; the decorated function
            if left out.
        ranges: Sampling intervals by symbol name; ``(0.5, 2)`` for the others.
        rtol: The relative tolerance of the comparison.
    """

    expr: Any
    implementation: Callable[..., Any] | None = None
    ranges: Mapping[str, tuple[float, float]] = field(default_factory=dict)
    rtol: float = 1e-10


@dataclass(frozen=True)
class ConvergenceProblem:
    """A test problem: the error of a method for a sequence of step sizes.

    Attributes:
        error: The error at one step size, or the errors by variable (keys of
            ``order``).
        steps: The step sizes, at least two, best halving each time.
        tolerance: How far the observed order may be from the declared one.
    """

    error: Callable[[float], float | Mapping[str, float]]
    steps: Sequence[float]
    tolerance: float = 0.1


def observed_order(steps: Sequence[float], errors: Sequence[float]) -> float:
    """The slope of ``log(error)`` against ``log(step)``, fitted by least squares.

    Raises:
        ValueError: With fewer than two steps or a non-positive error.
    """
    h, e = np.asarray(steps, float), np.asarray(errors, float)
    if h.size < 2 or h.shape != e.shape:
        raise ValueError("need at least two steps and one error per step")
    if np.any(e <= 0) or np.any(h <= 0):
        raise ValueError(f"errors and steps must be positive, got errors {e}")
    return float(np.polyfit(np.log(h), np.log(e), 1)[0])


def check_order(
    problem: ConvergenceProblem, order: int | Mapping[str, int]
) -> dict[str, float]:
    """Check the observed orders of a problem against the declared ones.

    Args:
        problem: The test problem.
        order: The declared order, an integer or one per variable.

    Returns:
        The observed order by variable (``"order"`` for a single one).

    Raises:
        AssertionError: If an observed order differs by more than the tolerance.
    """
    results = [problem.error(step) for step in problem.steps]
    expected = order if isinstance(order, Mapping) else {"order": order}
    errors: dict[str, list[float]] = {
        key: [r[key] if isinstance(r, Mapping) else float(r) for r in results]
        for key in expected
    }
    observed = {
        key: observed_order(problem.steps, values) for key, values in errors.items()
    }
    for key, value in observed.items():
        assert abs(value - expected[key]) <= problem.tolerance, (
            f"{key}: observed order {value:.3f}, declared {expected[key]}"
            f" (errors {errors[key]})"
        )
    return observed


def check_rule(
    rule: Any,
    implementation: Callable[..., Any] | None,
    *,
    samples: int = 16,
    seed: int = 0,
) -> None:
    """Compare a SymPy rule with the implementation on random inputs.

    Args:
        rule: A :class:`Rule` or a bare SymPy expression.
        implementation: The function used when the rule names none.
        samples: The number of random input sets.
        seed: The seed of the random inputs.

    Raises:
        TypeError: If there is nothing to call.
        AssertionError: If the values differ by more than the rule's tolerance.
    """
    import sympy

    rule = rule if isinstance(rule, Rule) else Rule(rule)
    call = rule.implementation or implementation
    if call is None or inspect.isclass(call):
        raise TypeError("a rule on a class needs Rule(expr, implementation=...)")
    symbols = sorted(rule.expr.free_symbols, key=lambda symbol: symbol.name)
    names = [symbol.name for symbol in symbols]
    # SciPy for the special functions (erf, ...) when it is there
    try:
        import scipy  # noqa: F401

        modules = ["scipy", "numpy"]
    except ImportError:  # pragma: no cover - SciPy is installed with the test extra
        modules = ["numpy"]
    expected = sympy.lambdify(symbols, rule.expr, modules=modules)
    rng = np.random.default_rng(seed)
    inputs = {
        name: rng.uniform(*rule.ranges.get(name, (0.5, 2.0)), size=samples)
        for name in names
    }
    want = np.broadcast_to(expected(*inputs.values()), (samples,))
    got = np.array(
        [
            call(**{name: values[i] for name, values in inputs.items()})
            for i in range(samples)
        ],
        dtype=float,
    )
    np.testing.assert_allclose(got, want, rtol=rule.rtol, atol=0)
