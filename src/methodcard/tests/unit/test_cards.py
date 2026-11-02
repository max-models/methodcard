"""Cards, the mixin, the decorator, the registry and rendering."""

import pytest
import toymethods
from toymethods.schemes import Drift, Kick, Leapfrog, SlowDrift, drift

import methodcard
from methodcard import MethodCard, NumericalMethod, card, describe, method, registry
from methodcard.registry import entries, load


def test_registry_is_keyed_per_package():
    assert set(registry("toymethods")) == {
        "toymethods.schemes.drift",
        "toymethods.schemes.Kick",
        "toymethods.schemes.Drift",
        "toymethods.schemes.Leapfrog",
    }
    assert registry("toymethods")["toymethods.schemes.Kick"] is Kick
    assert set(registry("toymethods")) <= set(registry())


def test_abstract_and_inheriting_classes_are_not_registered():
    assert "toymethods.schemes.Scheme" not in registry()
    assert "toymethods.schemes.SlowDrift" not in registry()
    assert SlowDrift.card() is Drift.card()
    with pytest.raises(LookupError, match="abstract"):
        toymethods.schemes.Scheme.card()


def test_card_of_function_and_class():
    assert card(drift).equations == {"update": r"x^{n+1} = x^n + v^n \Delta t"}
    assert card(drift).summary == "Advance a position at fixed velocity."
    assert card(Leapfrog).order == {"x": 2, "v": 2}
    assert card(Leapfrog).components == (
        "toymethods.schemes.Kick",
        "toymethods.schemes.Drift",
    )
    with pytest.raises(LookupError):
        card(len)
    with pytest.raises(LookupError):
        card(42)


def test_markdown_and_latex_rendering():
    text = Leapfrog()._repr_markdown_()
    assert text.startswith("**Leapfrog**: Kick, drift, kick.")
    assert "$$\nx^{n+1} = x^n + v^{n+1/2} \\Delta t\n$$" in text
    assert "*half kick*" in text
    assert "Order of accuracy: x: 2, v: 2." in text
    assert "- `toymethods.schemes.Kick`" in text
    assert "- `Propagators.leapfrog_symplectic`" in text
    assert card(Kick)._repr_markdown_().startswith("**Kick**")
    assert "References:\n\n- Hockney" in card(Kick)._repr_markdown_()
    assert (
        Kick()._repr_latex_()
        == r"$$\begin{aligned}v^{n+1} = v^n + a \Delta t\end{aligned}$$"
    )
    assert card(Kick)._repr_latex_() == Kick()._repr_latex_()


def test_describe():
    text = Leapfrog.describe()
    assert text.splitlines()[0] == "toymethods.schemes.Leapfrog: Kick, drift, kick."
    assert "  half_kick  v^{n+1/2}" in text
    assert "order: x: 2, v: 2" in text
    assert "built from: toymethods.schemes.Kick; toymethods.schemes.Drift" in text
    assert "lean: Propagators.leapfrog_symplectic" in text
    assert "see: Hockney" in describe(card(Kick))
    assert "assumes: velocity constant" in describe(card(drift))


def test_dict_round_trip():
    data = card(Leapfrog).to_dict()
    assert data["components"] == ["toymethods.schemes.Kick", "toymethods.schemes.Drift"]
    assert MethodCard.from_dict(data) == card(Leapfrog)


@pytest.mark.parametrize(
    ("fields", "message"),
    [
        ({"equations": {}}, "non-empty dict"),
        ({"equations": "x = 1"}, "non-empty dict"),
        ({"equations": {"Update": "x"}}, "snake_case"),
        ({"equations": {"update": ""}}, "LaTeX string"),
        ({"equations": {"update": "x"}, "order": 0}, "positive integer"),
        ({"equations": {"update": "x"}, "order": True}, "positive integer"),
        ({"equations": {"update": "x"}, "order": {}}, "empty dict"),
        ({"equations": {"update": "x"}, "order": {"X": 1}}, "snake_case"),
        (
            {"equations": {"update": "x"}, "assumptions": "uniform grid"},
            "tuple of strings",
        ),
        ({"equations": {"update": "x"}, "references": ("",)}, "non-empty strings"),
    ],
)
def test_validation(fields, message):
    with pytest.raises(TypeError, match=message):
        MethodCard.build("pkg.thing", **fields)


def test_mixin_needs_equations():
    with pytest.raises(TypeError, match="must declare equations"):

        class NoMath(NumericalMethod):
            pass


def test_decorator_validates_components():
    with pytest.raises(TypeError, match="components must be a tuple"):
        method(equations={"update": "x"}, components="Kick")(lambda: None)
    with pytest.raises(
        TypeError, match="symbolic must be a dict of SymPy rules or a function"
    ):
        method(equations={"update": "x"}, symbolic=["x"])(lambda: None)


def test_decorated_class_and_reregistration():
    @method(equations={"update": "y = 2 x"}, components=(drift, "other.method"))
    class Doubler:
        pass

    name = f"{__name__}.test_decorated_class_and_reregistration.<locals>.Doubler"
    assert entries()[name].card.components == (
        "toymethods.schemes.drift",
        "other.method",
    )
    assert entries()[name].card.summary == ""
    method(equations={"update": "y = 3 x"})(Doubler)
    assert entries()[name].card.equations == {"update": "y = 3 x"}


def test_load_reports_failed_modules(tmp_path, monkeypatch):
    package = tmp_path / "brokenpkg"
    (package / "tests").mkdir(parents=True)
    (package / "__init__.py").write_text("")
    (package / "good.py").write_text("X = 1\n")
    (package / "bad.py").write_text("import not_a_module_anywhere\n")
    (package / "tests" / "__init__.py").write_text(
        "raise RuntimeError('not imported')\n"
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    failed = load("brokenpkg")
    assert set(failed) == {"brokenpkg.bad"}
    assert isinstance(failed["brokenpkg.bad"], ModuleNotFoundError)


def test_version():
    assert methodcard.__version__


def test_lazy_rules():
    from methodcard.testing import _rule_keys

    assert list(entries()["toymethods.schemes.Drift"].rules()) == ["update"]

    def missing():
        raise ImportError("no sympy")

    @method(equations={"update": "x"}, symbolic=missing)
    def needs_sympy():
        """Rules that need SymPy."""

    name = f"{__name__}.test_lazy_rules.<locals>.needs_sympy"
    assert _rule_keys(entries()[name]) == []
