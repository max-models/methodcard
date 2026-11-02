"""Toy schemes: a drift function, kick and drift classes and their leapfrog."""

import math

import sympy

from methodcard import ConvergenceProblem, NumericalMethod, Rule, method

x, v, dt = sympy.symbols("x v dt")


@method(
    equations={"update": r"x^{n+1} = x^n + v^n \Delta t"},
    assumptions=("velocity constant over the step",),
    symbolic={"update": x + v * dt},
)
def drift(x, v, dt):
    """Advance a position at fixed velocity."""
    return x + v * dt


class Scheme(NumericalMethod, abstract=True):
    """An abstract scheme: no card."""


class Kick(Scheme):
    """Change the velocity by a constant acceleration."""

    equations = {"update": r"v^{n+1} = v^n + a \Delta t"}
    references = ("Hockney and Eastwood (1988), section 4-3",)
    symbolic = {
        "update": Rule(
            v + sympy.Symbol("a") * dt, implementation=lambda v, a, dt: v + a * dt
        )
    }


def _drift_rules():
    """The rules of Drift, built only when the tests ask for them."""
    return {"update": Rule(x + v * dt, implementation=lambda x, v, dt: x + v * dt)}


class Drift(Scheme):
    """Advance positions at fixed velocity."""

    equations = {"update": r"x^{n+1} = x^n + v^n \Delta t"}
    symbolic = staticmethod(_drift_rules)


class SlowDrift(Drift):
    """The same method as Drift: no equations of its own, so not registered again."""


def _oscillator_error(dt: float) -> dict[str, float]:
    """The leapfrog error on a harmonic oscillator after t = 1."""
    xs, vs = 1.0, 0.0
    steps = round(1.0 / dt)
    for _ in range(steps):
        vs -= 0.5 * dt * xs
        xs += dt * vs
        vs -= 0.5 * dt * xs
    return {"x": abs(xs - math.cos(1.0)), "v": abs(vs + math.sin(1.0))}


class Particle:
    """A particle with a kinetic energy."""

    def __init__(self, v: float) -> None:
        """Store the speed."""
        self.v = v

    @property
    @method(equations={"energy": r"E = \tfrac{1}{2} v^2"})
    def energy(self) -> float:
        """The kinetic energy per unit mass."""
        return 0.5 * self.v**2


class Leapfrog(Scheme):
    """Kick, drift, kick."""

    equations = {
        "half_kick": r"v^{n+1/2} = v^n + a(x^n) \Delta t / 2",
        "drift": r"x^{n+1} = x^n + v^{n+1/2} \Delta t",
    }
    order = {"x": 2, "v": 2}
    components = (Kick, Drift)
    lean_theorems = ("Propagators.leapfrog_symplectic",)

    @classmethod
    def convergence_problem(cls) -> ConvergenceProblem:
        """The harmonic oscillator."""
        return ConvergenceProblem(_oscillator_error, steps=(0.1, 0.05, 0.025, 0.0125))
