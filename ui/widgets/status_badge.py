from __future__ import annotations

import tkinter as tk

from ui.styles.theme import Palette
from ui.widgets.common import font, set_text
from utils.levels import Level


class StatusBadge(tk.Label):
    """Small pill showing Normal / Moderate / High / Critical (or an availability state)."""

    def __init__(self, parent: tk.Misc, palette: Palette, bg: str | None = None) -> None:
        super().__init__(parent, text="N/A", font=font(8, "bold"), padx=8, pady=1,
                         fg=palette.on_badge, bg=palette.muted)
        self._p = palette

    def set_level(self, level: Level) -> None:
        set_text(self, level.value.upper(), bg=self._p.color_for(level))

    def set_state(self, text: str, color: str) -> None:
        set_text(self, text.upper(), bg=color)
