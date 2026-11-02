"""Render a card: Markdown with ``$$`` math (docs, Jupyter), LaTeX and plain text."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from methodcard.card import MethodCard

#: The heading of the section appended to a docstring.
SECTION = "Numerics"


def order_text(order: int | dict[str, int] | None) -> str:
    """The order of accuracy in words: ``"2"`` or ``"x: 2, v: 1"``."""
    if order is None:
        return ""
    if isinstance(order, dict):
        return ", ".join(f"{key}: {value}" for key, value in order.items())
    return str(order)


def markdown(card: MethodCard, *, title: bool = False) -> str:
    """The card as Markdown, with each equation in a ``$$`` block.

    Args:
        card: The card.
        title: Start with the method's name and summary (for Jupyter), rather than
            the section heading of a docstring.

    Returns:
        The Markdown text.
    """
    if title:
        short = card.name.rsplit(".", 1)[-1]
        lines = [f"**{short}**" + (f": {card.summary}" if card.summary else ""), ""]
    else:
        lines = [f"**{SECTION}**", ""]
    for name, tex in card.equations.items():
        lines += [f"*{name.replace('_', ' ')}*", "", "$$", tex, "$$", ""]
    if card.order is not None:
        lines += [f"Order of accuracy: {order_text(card.order)}.", ""]
    for label, items in (
        ("Assumptions", card.assumptions),
        ("References", card.references),
        ("Built from", tuple(f"`{name}`" for name in card.components)),
        ("Lean theorems", tuple(f"`{name}`" for name in card.lean_theorems)),
    ):
        if items:
            lines += [f"{label}:", "", *(f"- {item}" for item in items), ""]
    return "\n".join(lines).rstrip() + "\n"


def latex(card: MethodCard) -> str:
    """All equations of the card in one ``aligned`` display block."""
    rows = r" \\ ".join(card.equations.values())
    return f"$$\\begin{{aligned}}{rows}\\end{{aligned}}$$"


def describe(card: MethodCard) -> str:
    """A plain-text summary for terminals."""
    lines = [card.name + (f": {card.summary}" if card.summary else "")]
    width = max(len(name) for name in card.equations)
    lines += [f"  {name:<{width}}  {tex}" for name, tex in card.equations.items()]
    if card.order is not None:
        lines.append(f"  order: {order_text(card.order)}")
    for label, items in (
        ("assumes", card.assumptions),
        ("see", card.references),
        ("built from", card.components),
        ("lean", card.lean_theorems),
    ):
        if items:
            lines.append(f"  {label}: " + "; ".join(items))
    return "\n".join(lines)
