from __future__ import annotations

import tkinter as tk
from typing import Optional, Sequence

from ui.styles.theme import Palette
from ui.widgets.common import font, set_text


class InfoGrid(tk.Frame):
    """Key/value rows laid out in ``columns`` column pairs. Labels are created once."""

    def __init__(self, parent: tk.Misc, palette: Palette, keys: Sequence[str], columns: int = 1,
                 value_wrap: int = 380) -> None:
        super().__init__(parent, bg=palette.surface, highlightbackground=palette.border,
                         highlightthickness=1, padx=14, pady=10)
        self._values: dict[str, tk.Label] = {}
        rows = -(-len(keys) // columns)
        for n, key in enumerate(keys):
            col, row = divmod(n, rows)
            tk.Label(self, text=key, font=font(9), fg=palette.muted, bg=palette.surface,
                     anchor="w").grid(row=row, column=col * 2, sticky="w", padx=(0, 14), pady=2)
            value = tk.Label(self, text="N/A", font=font(10, "bold"), fg=palette.text, bg=palette.surface,
                             anchor="w", justify="left", wraplength=value_wrap)
            value.grid(row=row, column=col * 2 + 1, sticky="w", padx=(0, 28), pady=2)
            self._values[key] = value
        for c in range(columns * 2):
            self.grid_columnconfigure(c, weight=1 if c % 2 else 0)

    def set(self, key: str, text: str, color: Optional[str] = None) -> None:
        label = self._values[key]
        if color:
            set_text(label, text, fg=color)
        else:
            set_text(label, text)
