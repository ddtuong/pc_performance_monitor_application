from __future__ import annotations

import tkinter as tk
from typing import Callable, Optional, Sequence

from ui.styles.theme import Palette
from ui.widgets.chart import ChartWidget
from ui.widgets.common import font, set_text


class ChartCard(tk.Frame):
    """Titled card around a ChartWidget, with a right-aligned note (e.g. 'N/A - no sensor')."""

    def __init__(self, parent: tk.Misc, palette: Palette, title: str, height: int = 150,
                 y_max: Optional[float] = 100.0, y_formatter: Optional[Callable[[float], str]] = None,
                 legend: Optional[Sequence[str]] = None, colors: Optional[Sequence[str]] = None) -> None:
        super().__init__(parent, bg=palette.surface, highlightbackground=palette.border,
                         highlightthickness=1, padx=10, pady=8)
        head = tk.Frame(self, bg=palette.surface)
        head.pack(fill="x")
        tk.Label(head, text=title, font=font(10, "bold"), fg=palette.text, bg=palette.surface).pack(side="left")
        self._note = tk.Label(head, text="", font=font(9), fg=palette.muted, bg=palette.surface)
        self._note.pack(side="right")
        self.chart = ChartWidget(self, palette, height=height, y_max=y_max, y_formatter=y_formatter,
                                 legend=legend, colors=colors)
        self.chart.pack(fill="both", expand=True, pady=(6, 0))

    def draw(self, series: Sequence[Sequence[Optional[float]]], span_seconds: float, capacity: int,
             empty_note: str = "") -> None:
        self.chart.set_axis(span_seconds, capacity)
        has_data = any(v is not None for s in series for v in s)
        set_text(self._note, "" if has_data else empty_note)
        self.chart.set_data(series)
