# methodcard


<!-- README.md is generated from README.qmd: edit the .qmd and run `make readme`. -->

[![Tests](https://github.com/max-models/methodcard/actions/workflows/test_pytest.yml/badge.svg)](https://github.com/max-models/methodcard/actions/workflows/test_pytest.yml)
[![Static
analysis](https://github.com/max-models/methodcard/actions/workflows/static_analysis.yml/badge.svg)](https://github.com/max-models/methodcard/actions/workflows/static_analysis.yml)
[![Docs](https://github.com/max-models/methodcard/actions/workflows/docs.yml/badge.svg)](https://max-models.github.io/methodcard/)
[![codecov](https://codecov.io/gh/max-models/methodcard/branch/main/graph/badge.svg)](https://codecov.io/gh/max-models/methodcard)
[![PyPI](https://img.shields.io/pypi/v/methodcard.png)](https://pypi.org/project/methodcard/)
[![Python](https://img.shields.io/pypi/pyversions/methodcard.png)](https://pypi.org/project/methodcard/)

The math of each numerical method, declared once and shown in its docs
and tests.

A class (with the `NumericalMethod` mixin) or a function (with the
`@method` decorator) declares its equations, order of accuracy,
assumptions and references, next to the code:

``` python
from methodcard import NumericalMethod


class Drift(Propagator, NumericalMethod):
    """Advance positions at fixed velocity."""

    equations = {"update": r"x^{n+1} = x^n + v^n \Delta t"}
    assumptions = ("velocity constant over the step",)
```

- **Jupyter and terminal**: a method renders its card in a notebook;
  `describe()` prints it.
- **Docs**: a griffe extension adds a “Numerics” section to each
  method’s API page, and `methodcard export` gives the catalogue of the
  shared
  [starlight-theme](https://github.com/max-models/starlight-theme)
  (`defineDocs({ methodcard: true })`), both without importing the code.
- **Tests**: `TestMethodCards = method_suite("mypackage")` checks every
  card: SymPy rules against the implementation, observed against
  declared orders, and the docs against the runtime.

Documentation: <https://max-models.github.io/methodcard/>

## Install

``` bash
pip install methodcard            # or methodcard[symbolic] for the SymPy checks
```

For development, with [uv](https://docs.astral.sh/uv/):

``` bash
make install    # uv sync --extra dev, plus the pre-commit hooks
```

## Development

Formatting and linting use [ruff](https://docs.astral.sh/ruff/), type
checking [pyright](https://microsoft.github.io/pyright/), run by
[pre-commit](https://pre-commit.com/) and in CI:

``` bash
make lint     # ruff check, ruff format --check, pyright
make test     # pytest with coverage
```

Commit messages follow [Conventional
Commits](https://www.conventionalcommits.org/); see
[CONTRIBUTING.md](CONTRIBUTING.md).

## Build docs

The documentation in `docs/` is an Astro + Starlight site: hand-written
pages, the notebooks in `tutorials/` executed and published as pages,
and the API reference generated from the docstrings with
[starlight-pydocs](https://ewels.github.io/starlight-pydocs/). It needs
Node 22 or newer.

``` bash
make docs-install     # npm packages and the Python docs extra
make docs-notebooks   # execute tutorials/*.ipynb and convert them to pages
make docs-dev         # live preview at http://localhost:4321/methodcard/
make docs-build       # the static site in docs/dist
```

## Build the README

`README.md` is rendered from `README.qmd` with
[Quarto](https://quarto.org/):

``` bash
make readme
```

## Releases

Before merging a release to `main`, update the version in
`pyproject.toml`, `src/methodcard/__init__.py` and `CITATION.cff`
(including its release date), and add the release notes to
`CHANGELOG.md`. The push to `main` creates a GitHub release with a
`vX.Y.Z` tag and publishes the package to PyPI with trusted publishing
(OIDC). The one-time PyPI and GitHub configuration is described in the
[publishing
tutorial](https://max-models.github.io/methodcard/development/publishing/).
