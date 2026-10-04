from __future__ import annotations

import tkinter as tk
from typing import Optional, Sequence

from ui.styles.theme import Palette
from ui.widgets.common import font, set_text
from ui.widgets.progress_card import UsageBar


class MetricCard(tk.Frame):
    """Dashboard-style card: title, big value, optional bar, up to N detail lines."""

    def __init__(self, parent: tk.Misc, palette: Palette, title: str, lines: int = 2,
                 show_bar: bool = True, value_size: int = 22) -> None:
        super().__init__(parent, bg=palette.surface, highlightbackground=palette.border,
                         highlightthickness=1, padx=14, pady=10)
        self._p = palette
        tk.Label(self, text=title.upper(), font=font(9, "bold"), fg=palette.muted,
                 bg=palette.surface, anchor="w").pack(fill="x")
        self._value = tk.Label(self, text="N/A", font=font(value_size, "bold"), fg=palette.text,
                               bg=palette.surface, anchor="w")
        self._value.pack(fill="x", pady=(2, 4))
        self._bar: Optional[UsageBar] = None
        if show_bar:
            self._bar = UsageBar(self, palette, height=6)
            self._bar.pack(fill="x", pady=(0, 6))
        self._lines = []
        for _ in range(lines):
            label = tk.Label(self, text="", font=font(9), fg=palette.muted, bg=palette.surface, anchor="w")
            label.pack(fill="x")
            self._lines.append(label)

    def update_card(self, value: str, lines: Sequence[str] = (), percent: Optional[float] = None,
                    color: Optional[str] = None) -> None:
        set_text(self._value, value, fg=color or self._p.text)
        if self._bar is not None:
            self._bar.set(percent, color)
        for i, label in enumerate(self._lines):
            set_text(label, lines[i] if i < len(lines) else "")
