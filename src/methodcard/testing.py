"""The generated tests of a package's cards.

One line in a test module of the package::

    from methodcard.testing import method_suite

    TestMethodCards = method_suite("freeofcharge")

gives a test class with, for every registered method of the package:

- ``test_card``: the card is complete (a docstring summary, components registered);
- ``test_docs_match``: the cards griffe reads for the docs equal the runtime ones;
- ``test_symbolic``: each SymPy rule matches the implementation (needs ``sympy``);
- ``test_convergence``: the observed order matches ``order`` (marker ``convergence``).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from methodcard.checks import check_order, check_rule
from methodcard.registry import Entry, entries, load


def _search_path(package: str) -> Path:
    """The directory that holds the package (``src`` in a src layout)."""
    spec = importlib.util.find_spec(package)
    if spec is None or not spec.submodule_search_locations:
        raise ModuleNotFoundError(f"{package} is not an installed package")
    return Path(next(iter(spec.submodule_search_locations))).parent


def method_suite(package: str) -> type:
    """A pytest test class checking every card of a package.

    Args:
        package: The top-level package; all its modules (outside ``tests``) are imported.

    Returns:
        The class; assign it to a name starting with ``Test``.
    """
    failed = load(package)
    found = entries(package)
    ids = list(found)
    rules = [(name, key) for name, entry in found.items() for key in entry.symbolic]
    problems = [name for name, entry in found.items() if entry.problem is not None]
    static: dict[str, dict] = {}

    def docs_cards() -> dict[str, dict]:
        if not static:
            from methodcard.export import export

            for card in export(package, [_search_path(package)])["cards"]:
                static[card["name"]] = card
        return static

    class MethodSuite:
        def test_modules_import(self) -> None:
            assert not failed, f"modules that failed to import: {failed}"

        def test_has_cards(self) -> None:
            assert found, f"{package} registers no method cards"

        @pytest.mark.parametrize("name", ids)
        def test_card(self, name: str) -> None:
            card = found[name].card
            assert card.summary, f"{name} needs a docstring"
            missing = [part for part in card.components if part not in entries()]
            assert not missing, f"{name}: components without a card: {missing}"

        @pytest.mark.parametrize("name", ids)
        def test_docs_match(self, name: str) -> None:
            cards = docs_cards()
            assert name in cards, (
                f"{name}: the docs do not see this card; write its metadata as"
                " literals in the class body or the @method(...) call"
            )
            fields = {key: cards[name][key] for key in found[name].card.to_dict()}
            assert fields == found[name].card.to_dict()

        def test_no_docs_only_cards(self) -> None:
            extra = sorted(set(docs_cards()) - set(found))
            assert not extra, (
                f"cards in the docs but not registered at runtime: {extra}"
            )

        @pytest.mark.parametrize(("name", "key"), rules)
        def test_symbolic(self, name: str, key: str) -> None:
            pytest.importorskip("sympy")
            entry: Entry = found[name]
            assert key in entry.card.equations, f"{name}: rule {key!r} has no equation"
            check_rule(entry.symbolic[key], entry.obj)

        @pytest.mark.convergence
        @pytest.mark.parametrize("name", problems)
        def test_convergence(self, name: str) -> None:
            entry = found[name]
            assert entry.card.order is not None, f"{name}: a problem but no order"
            assert entry.problem is not None
            check_order(entry.problem(), entry.card.order)

    MethodSuite.__name__ = MethodSuite.__qualname__ = f"MethodSuite[{package}]"
    return MethodSuite
