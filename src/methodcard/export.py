"""Read the cards of a package statically and export them as JSON (for the docs theme)."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any

import scope_profiler as sp

from methodcard._profiling import PROFILE_TAGS

#: The version of the JSON layout; the theme checks it.
SCHEMA = 1


def _objects(obj: Any) -> Iterator[Any]:
    """The object and its members, recursively, without aliases and test modules."""
    yield obj
    for member in obj.members.values():
        if member.is_alias or member.name == "tests":
            continue
        if member.is_module or member.is_class or member.is_function:
            yield from _objects(member)


@sp.profile("methodcard.export", tags=PROFILE_TAGS)
def export(package: str, search: Sequence[str | Path] = ("src",)) -> dict[str, Any]:
    """The cards of a package, read with griffe and the methodcard extension.

    Nothing is imported: this is what the API docs see.

    Args:
        package: The top-level package.
        search: Where griffe looks for it.

    Returns:
        ``{"schema", "package", "cards"}``; each card is ``MethodCard.to_dict()`` with
        ``kind`` (``"class"`` or ``"function"``), ``module``, ``filepath`` (relative to
        the search path) and ``lineno``.
    """
    import griffe

    from methodcard.griffe_extension import NAMESPACE, MethodcardExtension

    root = griffe.load(
        package,
        search_paths=[str(path) for path in search],
        extensions=griffe.load_extensions(MethodcardExtension()),
        docstring_parser="google",
    )
    filepath = root.filepath
    if not isinstance(filepath, Path):
        raise ValueError(f"{package} is a namespace package; give its directory")
    base = filepath.parent.parent if root.is_package else filepath.parent
    cards = []
    for obj in _objects(root):
        data = obj.extra.get(NAMESPACE)
        if data:
            cards.append(
                {
                    **data["card"],
                    "kind": data["kind"],
                    "module": obj.module.path,
                    "filepath": Path(obj.filepath).relative_to(base).as_posix(),  # type: ignore[arg-type]
                    "lineno": obj.lineno,
                }
            )
    cards.sort(key=lambda card: card["name"])
    return {"schema": SCHEMA, "package": package, "cards": cards}


def main(argv: Sequence[str] | None = None) -> int:
    """The ``methodcard`` command: ``methodcard export <package> [--search src] [-o file]``."""
    parser = argparse.ArgumentParser(prog="methodcard", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    cmd = commands.add_parser("export", help="write the cards of a package as JSON")
    cmd.add_argument("package")
    cmd.add_argument("--search", action="append", help="search path (default: src)")
    cmd.add_argument("-o", "--output", help="the JSON file (default: standard output)")
    args = parser.parse_args(argv)
    text = json.dumps(export(args.package, args.search or ["src"]), indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(text)
    else:
        sys.stdout.write(text)
    return 0
