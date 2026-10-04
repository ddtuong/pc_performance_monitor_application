from __future__ import annotations

import tkinter as tk
from typing import Callable, Sequence

from config.constants import APP_NAME
from ui.styles.theme import Palette
from ui.widgets.common import font


class Sidebar(tk.Frame):
    """Vertical navigation. Calls ``on_select(page_name)`` when an entry is clicked."""

    def __init__(self, parent: tk.Misc, palette: Palette, items: Sequence[str],
                 on_select: Callable[[str], None]) -> None:
        super().__init__(parent, bg=palette.surface, width=190)
        self.pack_propagate(False)
        self._p = palette
        self._on_select = on_select
        self._buttons: dict[str, tk.Label] = {}
        self._active = ""
        tk.Label(self, text=APP_NAME.upper(), font=font(10, "bold"), fg=palette.accent,
                 bg=palette.surface, wraplength=160, justify="left").pack(anchor="w", padx=18, pady=(20, 18))
        for item in items:
            button = tk.Label(self, text=item, font=font(11), fg=palette.text, bg=palette.surface,
                              anchor="w", padx=18, pady=9, cursor="hand2")
            button.pack(fill="x")
            button.bind("<Button-1>", lambda _e, name=item: self._on_select(name))
            button.bind("<Enter>", lambda _e, name=item: self._hover(name, True))
            button.bind("<Leave>", lambda _e, name=item: self._hover(name, False))
            self._buttons[item] = button

    def _hover(self, name: str, inside: bool) -> None:
        if name != self._active:
            self._buttons[name].configure(bg=self._p.surface_alt if inside else self._p.surface)

    def select(self, name: str) -> None:
        for key, button in self._buttons.items():
            active = key == name
            button.configure(bg=self._p.surface_alt if active else self._p.surface,
                             fg=self._p.accent if active else self._p.text,
                             font=font(11, "bold" if active else "normal"))
        self._active = name
