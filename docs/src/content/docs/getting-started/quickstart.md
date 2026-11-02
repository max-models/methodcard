---
title: Quickstart
description: Run the command line entry point of methodcard.
---

First, ensure that `methodcard` is [installed](/methodcard/getting-started/installation/).

## Basic usage

After installation, you can run the application with:

```bash
methodcard
```

which calls `methodcard.main.main` and prints a greeting.

## Use the package from Python

```python
from methodcard.main import main

main()
```

See the [API reference](/methodcard/api/methodcard/) for every module and function.

## Profiling

methodcard's coarse operations are [scope-profiler](https://github.com/max-models/scope-profiler)
regions (`methodcard.main` here), tagged with the opt-in tag `methodcard`: they are
off by default and cost a fraction of a microsecond per call. A code that profiles itself with
scope-profiler turns them on with the tag:

```python
import scope_profiler as sp

sp.setup(enable_tags=["methodcard"])
```

or without editing the code, with `SCOPE_PROFILER_ENABLE_TAGS=methodcard`,
`scope-profiler run --enable-tag methodcard` or `enable_tags = ["methodcard"]` in the
TOML configuration. New regions use `@sp.profile("methodcard.<name>", tags=PROFILE_TAGS)`
with `PROFILE_TAGS` from the package's `_profiling` module.
