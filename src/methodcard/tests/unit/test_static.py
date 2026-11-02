"""The griffe extension, the JSON export and the generated suite on broken packages."""

import json
import os
import textwrap
from pathlib import Path

import griffe
import pytest

import methodcard
from methodcard.export import SCHEMA, export, main
from methodcard.griffe_extension import NAMESPACE, MethodcardExtension
from methodcard.tests.conftest import DATA


def _package(tmp_path, name, **modules):
    package = tmp_path / name
    package.mkdir()
    for module, source in {"__init__": "", **modules}.items():
        (package / f"{module}.py").write_text(textwrap.dedent(source))
    return tmp_path


def _load(search, name):
    return griffe.load(
        name,
        search_paths=[str(search)],
        extensions=griffe.load_extensions(MethodcardExtension()),
        docstring_parser="google",
    )


def test_docstrings_get_the_numerics_section():
    root = _load(DATA, "toymethods")
    leapfrog = root["schemes.Leapfrog"]
    assert leapfrog.docstring.value.startswith("Kick, drift, kick.\n\n**Numerics**")
    assert "$$\nx^{n+1} = x^n + v^{n+1/2} \\Delta t\n$$" in leapfrog.docstring.value
    assert leapfrog.extra[NAMESPACE]["kind"] == "class"
    assert root["schemes.drift"].extra[NAMESPACE]["kind"] == "function"
    assert NAMESPACE not in root["schemes.Scheme"].extra
    assert NAMESPACE not in root["schemes.SlowDrift"].extra


def test_export_and_cli(tmp_path, capsys):
    data = export("toymethods", [DATA])
    assert data["schema"] == SCHEMA
    assert [card["name"].rsplit(".", 1)[-1] for card in data["cards"]] == [
        "Drift",
        "Kick",
        "Leapfrog",
        "drift",
    ]
    assert data["cards"][0]["filepath"] == "toymethods/schemes.py"
    out = tmp_path / "cards.json"
    assert main(["export", "toymethods", "--search", str(DATA), "-o", str(out)]) == 0
    assert json.loads(out.read_text()) == data
    main(["export", "toymethods", "--search", str(DATA)])
    assert json.loads(capsys.readouterr().out) == data


def test_edge_cases(tmp_path, caplog):
    search = _package(
        tmp_path,
        "edgy",
        parts="""
            from methodcard import NumericalMethod

            class Step(NumericalMethod):
                equations = {"update": "x"}
        """,
        __init__="from edgy.parts import Step\n",
        schemes='''
            import methodcard
            from edgy import Step
            from methodcard import NumericalMethod, method

            KEYS = ("uniform grid",)

            class Composite(NumericalMethod):
                equations: dict = {"update": "y"}
                components = (Step, "external.thing")
                assumptions = KEYS
                x, y = 1, 2

            class Undocumented(NumericalMethod):
                equations = {"update": "z"}

            @methodcard.method(equations={"Bad": "x"})
            def bad():
                """Invalid key."""

            @method(equations={"update": "x"}, order=2)
            class Decorated:
                """A decorated class."""

            class Plain:
                equations = {"update": "not a method"}

            class Abstract(NumericalMethod, abstract=True):
                equations = {"update": "abstract"}

            @staticmethod
            def other():
                pass
        ''',
    )
    with caplog.at_level("WARNING"):
        cards = {card["name"]: card for card in export("edgy", [search])["cards"]}
    assert set(cards) == {
        "edgy.parts.Step",
        "edgy.schemes.Composite",
        "edgy.schemes.Undocumented",
        "edgy.schemes.Decorated",
    }
    # a re-exported component resolves to where it is defined
    assert cards["edgy.schemes.Composite"]["components"] == [
        "edgy.parts.Step",
        "external.thing",
    ]
    assert cards["edgy.schemes.Composite"]["assumptions"] == []
    assert cards["edgy.schemes.Decorated"]["order"] == 2
    assert cards["edgy.schemes.Undocumented"]["summary"] == ""
    assert "Composite.assumptions is not a literal" in caplog.text
    assert "snake_case" in caplog.text
    root = _load(search, "edgy")
    assert root["schemes.Undocumented"].docstring.value.startswith("**Numerics**")


@pytest.fixture
def suite_project(pytester, monkeypatch):
    """A project using the suite, run in a subprocess so that its registry is its own."""
    src = str(Path(methodcard.__file__).parents[1])
    monkeypatch.setenv(
        "PYTHONPATH", os.pathsep.join(filter(None, [src, os.environ.get("PYTHONPATH")]))
    )

    def make(source):
        pytester.makepyfile(
            **{"badmethods/__init__.py": "", "badmethods/schemes.py": source}
        )
        pytester.makepyfile(
            test_cards="""
                from methodcard.testing import method_suite

                TestCards = method_suite("badmethods")
            """
        )
        pytester.syspathinsert()
        return pytester

    return make


def test_suite_reports_problems(suite_project):
    project = suite_project(
        '''
        import sympy
        from methodcard import ConvergenceProblem, NumericalMethod, method

        x = sympy.Symbol("x")
        NAMES = {"update": "x"}

        @method(equations=NAMES)
        def hidden():
            """Not literal, so the docs miss it."""

        @method(equations={"update": "x"}, symbolic={"update": 2 * x, "other": x})
        def wrong(x):
            """Wrong rule."""
            return x

        @method(equations={"update": "x"}, components=("nowhere.thing",))
        def orphan():
            pass

        @method(equations={"update": "x"}, problem=lambda: ConvergenceProblem(lambda h: h, (0.1, 0.05)))
        def no_order():
            """A problem without an order."""
        '''
    )
    result = project.runpytest_subprocess("-q", "-p", "no:cacheprovider")
    result.assert_outcomes(passed=9, failed=5)
    result.stdout.fnmatch_lines(
        [
            "*needs a docstring*",
            "*the docs do not see this card*",
            "*rule 'other' has no equation*",
            "*a problem but no order*",
        ]
    )


def test_suite_with_no_cards(suite_project):
    project = suite_project("X = 1\n")
    result = project.runpytest_subprocess("-q", "-p", "no:cacheprovider")
    result.stdout.fnmatch_lines(["*registers no method cards*"])


def test_suite_not_a_package():
    from methodcard.testing import _search_path

    with pytest.raises(ModuleNotFoundError):
        _search_path("json.decoder")
