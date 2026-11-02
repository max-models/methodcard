"""The scope-profiler tag of methodcard's profiling regions.

The regions are opt-in: :mod:`methodcard` registers the tag on import, so they
record nothing unless the application enables it, e.g. with
``scope_profiler.setup(enable_tags=["methodcard"])``.
"""

#: Tags of every methodcard region; the first is the opt-in tag.
PROFILE_TAGS = ("methodcard",)
