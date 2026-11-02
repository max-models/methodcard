"""The math of each numerical method, declared once and shown in its docs and tests."""

from importlib.metadata import PackageNotFoundError, version

import scope_profiler as sp

from methodcard._profiling import PROFILE_TAGS
from methodcard.base import NumericalMethod, method
from methodcard.card import MethodCard
from methodcard.checks import ConvergenceProblem, Rule, observed_order
from methodcard.registry import card, entries, load, registry
from methodcard.render import describe

try:
    __version__ = version("methodcard")
except PackageNotFoundError:  # not installed, e.g. run from a source tree
    __version__ = "0.0.0+unknown"

# The decorated functions pick the tag up, so registering after the imports is in time.
sp.register_opt_in_tag(*PROFILE_TAGS)

__all__ = [
    "ConvergenceProblem",
    "MethodCard",
    "NumericalMethod",
    "Rule",
    "card",
    "describe",
    "entries",
    "load",
    "method",
    "observed_order",
    "registry",
]
