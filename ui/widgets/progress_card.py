from __future__ import annotations

import tkinter as tk
from typing import Optional

from ui.styles.theme import Palette
from ui.widgets.common import font, set_text


class UsageBar(tk.Canvas):
    """Flat horizontal usage bar. Items are created once and only re-positioned."""

    def __init__(self, parent: tk.Misc, palette: Palette, height: int = 8, bg: Optional[str] = None) -> None:
        super().__init__(parent, height=height, bg=bg or palette.surface, highlightthickness=0, bd=0)
        self._bar_height = height
        self._percent = 0.0
        self._color = palette.accent
        self._trough = self.create_rectangle(0, 0, 0, height, width=0, fill=palette.surface_alt)
        self._fill = self.create_rectangle(0, 0, 0, height, width=0, fill=self._color)
        self.bind("<Configure>", lambda _e: self._redraw())

    def set(self, percent: Optional[float], color: Optional[str] = None) -> None:
        percent = max(0.0, min(100.0, percent or 0.0))
        color = color or self._color
        if percent == self._percent and color == self._color:
            return
        self._percent, self._color = percent, color
        self.itemconfigure(self._fill, fill=color)
        self._redraw()

    def _redraw(self) -> None:
        width = self.winfo_width()
        self.coords(self._trough, 0, 0, width, self._bar_height)
        self.coords(self._fill, 0, 0, width * self._percent / 100.0, self._bar_height)


class ProgressCard(tk.Frame):
    """Title + big value + usage bar + caption (used for RAM, swap, VRAM...)."""

    def __init__(self, parent: tk.Misc, palette: Palette, title: str) -> None:
        super().__init__(parent, bg=palette.surface, highlightbackground=palette.border,
                         highlightthickness=1, padx=14, pady=10)
        self._p = palette
        top = tk.Frame(self, bg=palette.surface)
        top.pack(fill="x")
        tk.Label(top, text=title.upper(), font=font(9, "bold"), fg=palette.muted,
                 bg=palette.surface).pack(side="left")
        self._percent = tk.Label(top, text="N/A", font=font(9, "bold"), fg=palette.muted, bg=palette.surface)
        self._percent.pack(side="right")
        self._value = tk.Label(self, text="N/A", font=font(18, "bold"), fg=palette.text,
                               bg=palette.surface, anchor="w")
        self._value.pack(fill="x", pady=(4, 6))
        self._bar = UsageBar(self, palette)
        self._bar.pack(fill="x")
        self._caption = tk.Label(self, text="", font=font(9), fg=palette.muted, bg=palette.surface, anchor="w")
        self._caption.pack(fill="x", pady=(6, 0))

    def update_card(self, value: str, percent: Optional[float], color: Optional[str], caption: str = "") -> None:
        set_text(self._value, value)
        set_text(self._percent, "N/A" if percent is None else f"{percent:.0f}%",
                 fg=color or self._p.muted)
        self._bar.set(percent, color)
        set_text(self._caption, caption)
