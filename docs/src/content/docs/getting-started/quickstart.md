---
title: Quickstart
description: Add method cards to a package, with their tests and docs.
---

First, ensure that `methodcard` is [installed](/methodcard/getting-started/installation/)
(`methodcard[symbolic]` for the SymPy checks).

## Declare the math

On a class, with the mixin next to its functional base:

```python
from methodcard import NumericalMethod


class Drift(Propagator, NumericalMethod):
    """Advance positions at fixed velocity."""

    equations = {"update": r"x^{n+1} = x^n + v^n \Delta t"}
    assumptions = ("velocity constant over the step",)
```

On a function, with the decorator:

```python
from methodcard import method


@method(
    equations={"attenuation": r"\frac{dN}{ds} = -n_e \sigma_s N"},
    order=2,
    references=("Suzuki et al., PPCF 40, 2097 (1998)",),
)
def deposit(beam, plasma, ds):
    """Attenuate the beam markers along their paths."""
```

Write the metadata as literals: the docs read it from the source, without importing the code.
See [Design](/methodcard/development/design/) for every field.

## Test it

One test module in the package:

```python
from methodcard.testing import method_suite

TestMethodCards = method_suite("mypackage")
```

and the `convergence` marker in `pyproject.toml`:

```toml
[tool.pytest]
ini_options.markers = ["convergence: an order-of-accuracy test of a method card"]
```

## Document it

In `docs/astro.config.mjs` of a site on the shared
[starlight-theme](https://github.com/max-models/starlight-theme):

```js
export default defineDocs({ /* ... */ methodcard: true });
```

Each method's API page then has a "Numerics" section, and `/numerics/` lists all cards. The
same data, as JSON:

```bash
methodcard export mypackage --search src -o cards.json
```

## Profiling

`methodcard.export` is a [scope-profiler](https://github.com/max-models/scope-profiler)
region with the opt-in tag `methodcard`, off unless enabled, e.g. with
`SCOPE_PROFILER_ENABLE_TAGS=methodcard`.
