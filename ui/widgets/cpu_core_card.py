from __future__ import annotations

import tkinter as tk
from typing import Optional

from ui.styles.theme import Palette
from ui.widgets.common import font, set_text
from ui.widgets.progress_card import UsageBar


class CPUCoreCard(tk.Frame):
    """One logical-processor tile: 'CPU n', usage %, frequency, mini bar."""

    def __init__(self, parent: tk.Misc, palette: Palette, index: int) -> None:
        super().__init__(parent, bg=palette.surface, highlightbackground=palette.border,
                         highlightthickness=1, padx=10, pady=8)
        self._p = palette
        tk.Label(self, text=f"CPU {index}", font=font(9, "bold"), fg=palette.muted,
                 bg=palette.surface).pack(anchor="w")
        self._usage = tk.Label(self, text="0%", font=font(18, "bold"), fg=palette.text, bg=palette.surface)
        self._usage.pack(pady=(2, 2))
        self._freq = tk.Label(self, text="", font=font(9), fg=palette.muted, bg=palette.surface)
        self._freq.pack()
        self._bar = UsageBar(self, palette, height=4)
        self._bar.pack(fill="x", pady=(6, 0))

    def update_card(self, usage: float, freq_text: str, color: str) -> None:
        set_text(self._usage, f"{usage:.0f}%", fg=color)
        set_text(self._freq, freq_text)
        self._bar.set(usage, color)
