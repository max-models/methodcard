"""The method card: the math a numerical method declares, and its validation."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any

#: The metadata fields, in the order the cards show them. All are literals (strings,
#: integers, dicts and tuples of them), so the docs can read them without importing the code.
FIELDS = (
    "equations",
    "order",
    "assumptions",
    "references",
    "lean_theorems",
    "components",
)

_KEY = re.compile(r"^[a-z][a-z0-9_]*$")


def _strings(name: str, value: Any, owner: str) -> tuple[str, ...]:
    """Check a sequence of strings and return it as a tuple."""
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise TypeError(f"{owner}: {name} must be a tuple of strings, got {value!r}")
    if not all(isinstance(item, str) and item for item in value):
        raise TypeError(f"{owner}: {name} must hold non-empty strings, got {value!r}")
    return tuple(value)


def _key(name: str, key: Any, owner: str) -> str:
    """Check a snake_case key of ``equations`` or ``order``."""
    if not isinstance(key, str) or not _KEY.match(key):
        raise TypeError(f"{owner}: {name} keys must be snake_case strings, got {key!r}")
    return key


def _order(value: Any, owner: str) -> int | dict[str, int] | None:
    """Check an order of accuracy: ``None``, a positive integer, or one per variable."""
    if value is None:
        return None
    if isinstance(value, Mapping):
        if not value:
            raise TypeError(f"{owner}: order must not be an empty dict")
        return {
            _key("order", key, owner): _order(item, owner)
            for key, item in value.items()
        }  # type: ignore[misc]
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise TypeError(f"{owner}: order must be a positive integer, got {value!r}")
    return value


@dataclass(frozen=True)
class MethodCard:
    """The math of one numerical method.

    Build it with :meth:`MethodCard.build`, which validates the fields; the mixin
    :class:`~methodcard.NumericalMethod` and the decorator :func:`~methodcard.method`
    do that for you.

    Attributes:
        name: The qualified name, ``<module>.<qualname>``.
        equations: Named LaTeX equations, e.g. ``{"update": r"x^{n+1} = x^n"}``.
        order: The expected order of accuracy, one per variable if they differ.
        assumptions: Preconditions in plain words, such as ``"uniform grid"``.
        references: Papers or textbook sections.
        lean_theorems: Fully qualified names of Lean theorems about the scheme.
        components: For a composite scheme, the qualified names of its parts.
        summary: The first line of the docstring.
    """

    name: str
    equations: dict[str, str]
    order: int | dict[str, int] | None = None
    assumptions: tuple[str, ...] = ()
    references: tuple[str, ...] = ()
    lean_theorems: tuple[str, ...] = ()
    components: tuple[str, ...] = ()
    summary: str = ""

    @classmethod
    def build(
        cls,
        name: str,
        *,
        equations: Mapping[str, str],
        order: int | Mapping[str, int] | None = None,
        assumptions: Sequence[str] = (),
        references: Sequence[str] = (),
        lean_theorems: Sequence[str] = (),
        components: Sequence[str] = (),
        summary: str = "",
    ) -> MethodCard:
        """Validate the fields and build the card.

        Args:
            name: The qualified name of the method.
            equations: Named LaTeX equations; at least one.
            order: The order of accuracy, an integer or one per variable.
            assumptions: Preconditions in plain words.
            references: Papers or textbook sections.
            lean_theorems: Qualified names of Lean theorems.
            components: Qualified names of the methods a composite scheme is built from.
            summary: The first line of the docstring.

        Returns:
            The card.

        Raises:
            TypeError: If a field has the wrong type, or ``equations`` is empty.
        """
        if not isinstance(equations, Mapping) or not equations:
            raise TypeError(f"{name}: equations must be a non-empty dict")
        checked = {}
        for key, tex in equations.items():
            if not isinstance(tex, str) or not tex.strip():
                raise TypeError(f"{name}: equation {key!r} must be a LaTeX string")
            checked[_key("equations", key, name)] = tex.strip()
        return cls(
            name=name,
            equations=checked,
            order=_order(order, name),
            assumptions=_strings("assumptions", assumptions, name),
            references=_strings("references", references, name),
            lean_theorems=_strings("lean_theorems", lean_theorems, name),
            components=_strings("components", components, name),
            summary=summary,
        )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> MethodCard:
        """Rebuild a card from :meth:`to_dict`, e.g. from the JSON export."""
        fields = {key: data[key] for key in (*FIELDS, "summary") if key in data}
        return cls.build(data["name"], **fields)

    def to_dict(self) -> dict[str, Any]:
        """The card as plain JSON-ready data (tuples become lists)."""
        data = asdict(self)
        for key in ("assumptions", "references", "lean_theorems", "components"):
            data[key] = list(data[key])
        return data

    def _repr_markdown_(self) -> str:
        from methodcard.render import markdown

        return markdown(self, title=True)

    def _repr_latex_(self) -> str:
        from methodcard.render import latex

        return latex(self)
