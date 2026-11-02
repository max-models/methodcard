---
title: Design
description: The card schema, how the docs and tests read it, and the rules that keep them in step.
---

Every numerical component (a scheme, an interpolator, a fit, a physics model) carries its own
math: the equations it implements, its order of accuracy, its assumptions and its sources.
That metadata lives on the code, renders in docs and Jupyter, and drives automated checks.

- **One source of truth.** Each equation is written once, on the class or function that
  implements it.
- **Discoverable.** `card(obj)` and `describe()` in a REPL, the card in Jupyter, the same math
  on the API page.
- **Testable.** Every declared property (SymPy rule, order) is checked in CI.
- **General.** Classes in any hierarchy and plain functions alike.

## Two ways to declare a card

The functional class tree of a package (`Propagator`, `Interpolator`, ...) says what a
component does. The `NumericalMethod` mixin cuts across it and only declares the math:

```python
class Drift(Propagator, NumericalMethod): ...
```

Functions, and classes that should not get the mixin, use the decorator with the same fields:

```python
@method(equations={"update": r"x^{n+1} = x^n + v^n \Delta t"})
def drift(x, v, dt): ...
```

Rules:

- The mixin holds metadata and display only: no physics, no state, no `__init__`.
- Abstract bases pass `abstract=True` (`class Scheme(NumericalMethod, abstract=True)`). A
  concrete class must declare `equations` in its own body; a subclass of a method that declares
  none is the same method and is not registered again.
- A composite scheme (leapfrog = kick + drift + kick) is a method of its own and names its parts
  in `components`.
- Tooling finds methods through the registry, `registry("mypackage")`, never through
  hand-written lists. `load("mypackage")` imports all modules (outside `tests`) to fill it.

## The fields

| Field | Type | Purpose |
| --- | --- | --- |
| `equations` | `dict[str, str]` | Required. Named LaTeX equations: `update`, `stencil`, `boundary`, ... |
| `order` | `int` or `dict[str, int]` | Expected order of accuracy, per variable if needed (`{"x": 2, "v": 2}`) |
| `assumptions` | `tuple[str, ...]` | Preconditions in plain words: `"uniform grid"`, validity ranges of a fit |
| `references` | `tuple[str, ...]` | Papers or textbook sections |
| `lean_theorems` | `tuple[str, ...]` | Qualified names of Lean theorems about the scheme |
| `components` | `tuple` | The methods a composite scheme is built from |
| `symbolic` | `dict[str, sympy.Expr \| Rule]` | Runtime only: SymPy rules by equation key |
| `convergence_problem` / `problem=` | callable | Runtime only: returns a `ConvergenceProblem` |

Conventions: equation keys are short snake_case names, stable over time since tests and docs
refer to them; LaTeX uses a superscript `n` for the time level and a subscript `i` for the grid
index.

## How the docs read the cards

The API reference of the max-models sites is built by
[starlight-pydocs](https://ewels.github.io/starlight-pydocs/), which runs
[griffe](https://mkdocstrings.github.io/griffe/) as **static analysis**: nothing is imported.
Changing `__doc__` at class creation would never reach the pages. Instead:

- `methodcard.griffe_extension` finds the `@method(...)` calls and the class bodies that assign
  `equations`, reads the fields with `ast.literal_eval`, appends a **Numerics** section (Markdown
  with `$$` math, rendered by the site's KaTeX with its macros) to the docstring, and stores the
  card in `obj.extra["methodcard"]`;
- `methodcard export` runs the same extension and writes all cards as JSON, which the theme
  turns into the catalogue page.

So the fields must be **literals** in the source. Components may also be names of other methods;
they resolve to where those are defined. The generated test `test_docs_match` fails when the
static view and the runtime registry disagree, e.g. when `equations` is built from a variable.

## The checks

`method_suite("mypackage")` returns a test class that runs, for every card of the package:

| Test | Runs for | Checks |
| --- | --- | --- |
| `test_card` | every card | a docstring summary; the components are registered |
| `test_docs_match` | every card | the card griffe reads equals the runtime one |
| `test_symbolic` | each `symbolic` rule | the implementation matches the SymPy rule on random inputs (via `lambdify`) |
| `test_convergence` | a convergence problem | the observed order is within the tolerance (0.1) of `order` |

A bare SymPy expression on a function is evaluated with the function itself, its symbols named
after the parameters. `Rule(expr, implementation=..., ranges=..., rtol=...)` covers classes and
other signatures. The convergence tests carry the `convergence` marker, so a slow suite can skip
them (`-m "not convergence"`) and run them nightly.

## Lean, later

The `lean_theorems` field is kept, but not checked yet. Proofs will live in one shared Lean
project (Mathlib built once), with proofs namespaced by package, a SymPy-to-Lean generator for
simple update rules, and a check here that the named theorems exist. The chain would then be:
Lean proves properties of the real-number scheme, SymPy states the same scheme, and the
implementation is tested against SymPy. The Lean-to-SymPy link is generated, not proven.

## Limitations

- Lean proofs are about real-number math, not floating point or the Python code.
- Convergence tests confirm the order on the chosen problems, not in general.
- Not goals: proving the Python implementation correct, or generating code from SymPy or Lean.
