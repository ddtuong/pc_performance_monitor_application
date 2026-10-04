"""Tiny helpers shared by widgets. Updating a Tk option costs a redraw, so skip no-ops."""
from __future__ import annotations

import tkinter as tk
from typing import Any

from ui.styles.theme import FONT


def font(size: int = 10, weight: str = "normal") -> tuple[str, int, str]:
    return (FONT, size, weight)


def set_text(widget: tk.Widget, text: str, **options: Any) -> None:
    """Configure a widget only when something actually changed."""
    changes = {} if str(widget.cget("text")) == text else {"text": text}
    for key, value in options.items():
        if str(widget.cget(key)) != str(value):
            changes[key] = value
    if changes:
        widget.configure(**changes)
