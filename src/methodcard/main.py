"""Main module of the python package."""

import scope_profiler as sp

from methodcard._profiling import PROFILE_TAGS


@sp.profile("methodcard.main", tags=PROFILE_TAGS)
def main() -> None:
    """Print a greeting; the entry point of the ``methodcard`` command."""
    print("Hello, world")
