"""The registry of every method card, filled on import and keyed by qualified name."""

from __future__ import annotations

import importlib
import pkgutil
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from methodcard.card import MethodCard


@dataclass(frozen=True)
class Entry:
    """A registered method: the object, its card and what only exists at runtime.

    Attributes:
        obj: The class or function.
        card: Its card.
        symbolic: SymPy rules by equation key (:class:`~methodcard.Rule` or bare
            expressions), or a function returning them.
        problem: Returns the :class:`~methodcard.ConvergenceProblem` of the method.
    """

    obj: Any
    card: MethodCard
    symbolic: Mapping[str, Any] | Callable[[], Mapping[str, Any]] = field(
        default_factory=dict
    )
    problem: Callable[[], Any] | None = None

    def rules(self) -> Mapping[str, Any]:
        """The SymPy rules, calling the function that returns them if need be."""
        return self.symbolic() if callable(self.symbolic) else self.symbolic

    @property
    def package(self) -> str:
        """The top-level package the method belongs to."""
        return self.card.name.split(".", 1)[0]


_REGISTRY: dict[str, Entry] = {}


def qualified_name(obj: Any) -> str:
    """``<module>.<qualname>`` of a class or function."""
    return f"{obj.__module__}.{obj.__qualname__}"


def summary(obj: Any) -> str:
    """The first line of the object's own docstring."""
    doc = obj.__dict__.get("__doc__") if isinstance(obj, type) else obj.__doc__
    return doc.strip().splitlines()[0].strip() if doc and doc.strip() else ""


def register(entry: Entry) -> None:
    """Add an entry; a name registered twice (a module reloaded) is replaced."""
    _REGISTRY[entry.card.name] = entry


def entries(package: str | None = None) -> dict[str, Entry]:
    """The registered entries, of one top-level package or of all.

    Args:
        package: The top-level package, e.g. ``"freeofcharge"``; ``None`` for all.

    Returns:
        A copy of the registry, ``{qualified name: entry}``.
    """
    return {
        name: entry
        for name, entry in _REGISTRY.items()
        if package is None or entry.package == package
    }


def registry(package: str | None = None) -> dict[str, Any]:
    """The registered classes and functions, of one top-level package or of all."""
    return {name: entry.obj for name, entry in entries(package).items()}


def card(obj: Any) -> MethodCard:
    """The card of a registered class or function (it renders in Jupyter).

    Raises:
        LookupError: If the object has no card.
    """
    try:
        return _REGISTRY[qualified_name(obj)].card
    except (KeyError, AttributeError):
        raise LookupError(f"{obj!r} has no method card") from None


def load(package: str) -> dict[str, BaseException]:
    """Import a package and all its submodules, so that every card is registered.

    Modules in a ``tests`` subpackage are skipped.

    Args:
        package: The top-level package.

    Returns:
        The modules that failed to import, with their errors.
    """
    failed: dict[str, BaseException] = {}
    todo = [importlib.import_module(package)]
    while todo:
        parent = todo.pop()
        for info in pkgutil.iter_modules(
            getattr(parent, "__path__", []), f"{parent.__name__}."
        ):
            if info.name.rsplit(".", 1)[-1] == "tests":
                continue
            try:
                module = importlib.import_module(info.name)
            except (
                Exception
            ) as error:  # an optional dependency, say; reported, not raised
                failed[info.name] = error
                continue
            if info.ispkg:
                todo.append(module)
    return failed
