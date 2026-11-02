"""A griffe extension: the cards read statically, for the API docs (starlight-pydocs).

griffe reads the source without importing it, so the extension takes the metadata from
the ``@method(...)`` call or the class body, appends a "Numerics" section to the
docstring and stores the card in ``obj.extra["methodcard"]``. Use it as
``griffe -e methodcard.griffe_extension`` or in the theme with
``defineDocs({ methodcard: true })``.
"""

from __future__ import annotations

import ast
from typing import Any, TypeGuard

from griffe import Class, Docstring, Extension, Function, Object, logger

from methodcard.card import FIELDS, MethodCard
from methodcard.render import markdown

#: Where the cards are stored in ``obj.extra``.
NAMESPACE = "methodcard"


def _is_method_decorator(node: ast.expr) -> TypeGuard[ast.Call]:
    """Whether a decorator is a call of ``method`` (or ``methodcard.method``)."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
    return name == "method"


def _literal(owner: str, field: str, node: ast.expr, resolve: Any) -> Any:
    """Evaluate a literal field; components may also be names of other methods."""
    if field == "components" and isinstance(node, (ast.Tuple, ast.List)):
        return tuple(
            item.value if isinstance(item, ast.Constant) else resolve(ast.unparse(item))
            for item in node.elts
        )
    try:
        return ast.literal_eval(node)
    except ValueError:
        logger.warning(
            "methodcard: %s.%s is not a literal, left out of the docs", owner, field
        )
        return None


def _resolver(obj: Object) -> Any:
    """Resolve a name in the scope of an object to its canonical path."""

    def resolve(name: str) -> str:
        head, _, rest = name.partition(".")
        try:
            path = obj.parent.resolve(head) if obj.parent else head  # type: ignore[union-attr]
        except Exception:
            path = head
        return f"{path}.{rest}" if rest else path

    return resolve


def _fields_from_call(obj: Object, call: ast.Call) -> dict[str, Any]:
    resolve = _resolver(obj)
    return {
        keyword.arg: _literal(obj.path, keyword.arg, keyword.value, resolve)
        for keyword in call.keywords
        if keyword.arg in FIELDS
    }


def _fields_from_body(cls: Class, node: ast.ClassDef) -> dict[str, Any]:
    resolve = _resolver(cls)
    fields: dict[str, Any] = {}
    for statement in node.body:
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
            target, value = statement.targets[0], statement.value
        elif isinstance(statement, ast.AnnAssign) and statement.value is not None:
            target, value = statement.target, statement.value
        else:
            continue
        if isinstance(target, ast.Name) and target.id in FIELDS:
            fields[target.id] = _literal(cls.path, target.id, value, resolve)
    return fields


def _canonical(obj: Object, path: str) -> str:
    """The path where an object is defined, following re-exports."""
    try:
        target = obj.modules_collection.get_member(path)
        return target.final_target.path if target.is_alias else target.path
    except Exception:
        return path


def attach(obj: Object, fields: dict[str, Any]) -> MethodCard | None:
    """Build the card of an object, store it and append it to the docstring."""
    fields = {key: value for key, value in fields.items() if value is not None}
    if "components" in fields:
        fields["components"] = tuple(
            _canonical(obj, path) for path in fields["components"]
        )
    doc = obj.docstring.value if obj.docstring else ""
    summary = doc.strip().splitlines()[0].strip() if doc.strip() else ""
    try:
        card = MethodCard.build(obj.path, summary=summary, **fields)
    except TypeError as error:
        logger.warning("methodcard: %s", error)
        return None
    obj.extra[NAMESPACE] = {"card": card.to_dict(), "kind": obj.kind.value}
    section = markdown(card)
    if obj.docstring:
        obj.docstring.value = f"{doc.rstrip()}\n\n{section}"
    else:
        obj.docstring = Docstring(section, parent=obj)
    return card


class MethodcardExtension(Extension):
    """Find the method cards while griffe visits the code.

    The cards are built once the package is loaded, so that the components of a
    composite scheme resolve to where they are defined.
    """

    def __init__(self) -> None:
        """Start with no cards found."""
        super().__init__()
        self._found: list[tuple[Object, dict[str, Any]]] = []

    def on_function_instance(
        self, *, node: ast.AST | Any, func: Function, **kwargs: Any
    ) -> None:
        """A function decorated with ``@method(...)``."""
        for decorator in getattr(node, "decorator_list", ()):
            if _is_method_decorator(decorator):
                self._found.append((func, _fields_from_call(func, decorator)))
                return

    def on_class_members(
        self, *, node: ast.AST | Any, cls: Class, **kwargs: Any
    ) -> None:
        """A class decorated with ``@method(...)``, or with ``equations`` in its body."""
        if not isinstance(node, ast.ClassDef):
            return
        for decorator in node.decorator_list:
            if _is_method_decorator(decorator):
                self._found.append((cls, _fields_from_call(cls, decorator)))
                return
        if (
            any(keyword.arg == "abstract" for keyword in node.keywords)
            or not node.bases
        ):
            return
        fields = _fields_from_body(cls, node)
        if "equations" in fields:
            self._found.append((cls, fields))

    def on_package(self, *, pkg: Any, **kwargs: Any) -> None:
        """Build the cards of the package that has been loaded."""
        found, self._found = self._found, []
        for obj, fields in found:
            attach(obj, fields)
