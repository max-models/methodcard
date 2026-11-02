# Changelog

All notable changes to this project are documented in this file and maintained manually. The
format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- `MethodCard`: the math of a numerical method (equations, order, assumptions, references,
  Lean theorems, components), validated on construction.
- `NumericalMethod` mixin and `@method(...)` decorator, which register the cards per package
  (`registry`, `entries`, `card`, `load`); cards render in Jupyter (`_repr_markdown_`,
  `_repr_latex_`) and as text (`describe`).
- `methodcard.griffe_extension`: reads the cards statically and adds a "Numerics" section to the
  docstrings, for starlight-pydocs; `methodcard export` writes them as JSON.
- `methodcard.testing.method_suite`: generated tests for a package's cards (SymPy rules,
  orders of convergence, docs against runtime); `Rule`, `ConvergenceProblem`, `observed_order`.
- Docs: the "Method cards" notebook and the design page.
- The griffe extension leaves the attributes that declare a card (`equations`, `order`, ...)
  out of the API reference; the "Numerics" section shows them.

### Removed

- The template's `main` entry point and example script.
