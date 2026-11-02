"""Declare the math of a method: the ``NumericalMethod`` mixin and the ``@method`` decorator."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any, ClassVar, TypeVar

from methodcard.card import MethodCard
from methodcard.registry import Entry, qualified_name, register, summary

T = TypeVar("T")


def _components(items: Sequence[Any], owner: str) -> tuple[str, ...]:
    """Qualified names of the components (classes, functions or names)."""
    if isinstance(items, str) or not isinstance(items, Sequence):
        raise TypeError(f"{owner}: components must be a tuple, got {items!r}")
    return tuple(
        item if isinstance(item, str) else qualified_name(item) for item in items
    )


def _symbolic(rules: Any, owner: str) -> Mapping[str, Any] | Callable[[], Any]:
    """Check that the SymPy rules are a dict, or a function that returns one."""
    if rules is None:
        return {}
    if callable(rules):
        return rules
    if not isinstance(rules, Mapping):
        raise TypeError(
            f"{owner}: symbolic must be a dict of SymPy rules or a function"
        )
    return dict(rules)


def method(
    *,
    equations: Mapping[str, str],
    order: int | Mapping[str, int] | None = None,
    assumptions: Sequence[str] = (),
    references: Sequence[str] = (),
    lean_theorems: Sequence[str] = (),
    components: Sequence[Any] = (),
    symbolic: Mapping[str, Any] | Callable[[], Mapping[str, Any]] | None = None,
    problem: Callable[[], Any] | None = None,
) -> Callable[[T], T]:
    r"""Attach a card to a function or class and register it.

    The metadata must be written as literals in the call, so that the docs can read it
    without importing the code. ``symbolic`` and ``problem`` are only used by the tests.

    Args:
        equations: Named LaTeX equations, e.g. ``{"update": r"x^{n+1} = x^n + v^n \Delta t"}``.
        order: The expected order of accuracy, an integer or one per variable.
        assumptions: Preconditions in plain words.
        references: Papers or textbook sections.
        lean_theorems: Qualified names of Lean theorems about the scheme.
        components: The methods a composite scheme is built from (objects or names).
        symbolic: SymPy rules by equation key, checked against the implementation; or
            a function returning them, so that the package imports SymPy only in tests.
        problem: Returns a :class:`~methodcard.ConvergenceProblem`, checked against ``order``.

    Returns:
        The decorator, which returns the object unchanged.
    """

    def decorate(obj: T) -> T:
        name = qualified_name(obj)
        card = MethodCard.build(
            name,
            equations=equations,
            order=order,
            assumptions=assumptions,
            references=references,
            lean_theorems=lean_theorems,
            components=_components(components, name),
            summary=summary(obj),
        )
        register(Entry(obj, card, _symbolic(symbolic, name), problem))
        return obj

    return decorate


class NumericalMethod:
    r"""Mixin for a class that implements a numerical method.

    A concrete subclass declares its math as class attributes, written as literals;
    only ``equations`` is required::

        class Drift(Propagator, NumericalMethod):
            \"\"\"Advance positions at fixed velocity.\"\"\"

            equations = {"update": r"x^{n+1} = x^n + v^n \Delta t"}
            assumptions = ("velocity constant over the step",)

    Abstract bases pass ``abstract=True`` (``class Scheme(NumericalMethod,
    abstract=True)``) and need no equations. A subclass of a method that declares no
    ``equations`` of its own is the same method: it is not registered again. The mixin
    holds no state and defines no ``__init__``.
    """

    equations: ClassVar[Mapping[str, str]] = {}
    order: ClassVar[int | Mapping[str, int] | None] = None
    assumptions: ClassVar[Sequence[str]] = ()
    references: ClassVar[Sequence[str]] = ()
    lean_theorems: ClassVar[Sequence[str]] = ()
    components: ClassVar[Sequence[Any]] = ()
    symbolic: ClassVar[Mapping[str, Any] | Callable[[], Mapping[str, Any]] | None] = (
        None
    )

    def __init_subclass__(cls, abstract: bool = False, **kwargs: Any) -> None:
        """Validate and register a concrete subclass."""
        super().__init_subclass__(**kwargs)
        if abstract:
            return
        if "equations" not in cls.__dict__:
            if any("_methodcard" in base.__dict__ for base in cls.__mro__[1:]):
                return
            raise TypeError(
                f"{cls.__qualname__} must declare equations (or abstract=True)"
            )
        name = qualified_name(cls)
        card = MethodCard.build(
            name,
            equations=cls.equations,
            order=cls.order,
            assumptions=cls.assumptions,
            references=cls.references,
            lean_theorems=cls.lean_theorems,
            components=_components(cls.components, name),
            summary=summary(cls),
        )
        cls._methodcard = card
        problem = getattr(cls, "convergence_problem", None)
        register(
            Entry(cls, card, _symbolic(getattr(cls, "symbolic", None), name), problem)
        )

    @classmethod
    def describe(cls) -> str:
        """A plain-text summary of the method's math."""
        from methodcard.render import describe

        return describe(cls.card())

    @classmethod
    def card(cls) -> MethodCard:
        """The method's card."""
        for base in cls.__mro__:
            if "_methodcard" in base.__dict__:
                return base.__dict__["_methodcard"]
        raise LookupError(f"{cls.__qualname__} is abstract and has no card")

    def _repr_markdown_(self) -> str:
        from methodcard.render import markdown

        return markdown(self.card(), title=True)

    def _repr_latex_(self) -> str:
        from methodcard.render import latex

        return latex(self.card())
