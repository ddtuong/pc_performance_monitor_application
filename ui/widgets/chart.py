from __future__ import annotations

import tkinter as tk
from typing import Callable, Optional, Sequence

from ui.styles.theme import Palette
from ui.widgets.common import font
from utils.scale import nice_ceiling


class ChartWidget(tk.Canvas):
    """Lightweight line chart on a Canvas. Right edge = now; ``None`` values are gaps."""
    PAD_L, PAD_R, PAD_T, PAD_B = 58, 12, 8, 22

    def __init__(self, parent: tk.Misc, palette: Palette, height: int = 150, y_max: Optional[float] = 100.0,
                 y_formatter: Optional[Callable[[float], str]] = None,
                 colors: Optional[Sequence[str]] = None, legend: Optional[Sequence[str]] = None) -> None:
        super().__init__(parent, height=height, bg=palette.surface, highlightthickness=0, bd=0)
        self._p = palette
        self._y_max = y_max
        self._fmt = y_formatter or (lambda v: f"{v:.0f}%")
        self._colors = tuple(colors) if colors else palette.chart_colors
        self._legend = list(legend) if legend else []
        self._span_s = 60.0
        self._capacity = 60
        self._data: list[list[Optional[float]]] = []
        self.bind("<Configure>", lambda _e: self.redraw())

    def set_axis(self, span_seconds: float, capacity: int) -> None:
        self._span_s, self._capacity = span_seconds, max(2, capacity)

    def set_data(self, series: Sequence[Sequence[Optional[float]]]) -> None:
        self._data = [list(s) for s in series]
        self.redraw()

    def redraw(self) -> None:
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 120 or h < 60:
            return
        left, right, top, bottom = self.PAD_L, w - self.PAD_R, self.PAD_T, h - self.PAD_B
        peak = max((v for s in self._data for v in s if v is not None), default=0.0)
        y_max = self._y_max or nice_ceiling(peak * 1.1)
        for frac in (0, 0.25, 0.5, 0.75, 1):
            y = bottom - (bottom - top) * frac
            self.create_line(left, y, right, y, fill=self._p.border)
            self.create_text(left - 6, y, text=self._fmt(y_max * frac), anchor="e",
                             fill=self._p.muted, font=font(8))
        for frac in (0, 0.25, 0.5, 0.75, 1):
            x = left + (right - left) * frac
            label = "Now" if frac == 1 else f"{self._span_s * (1 - frac):.0f}s"
            self.create_text(x, bottom + 4, text=label, anchor="n", fill=self._p.muted, font=font(8))
        step = (right - left) / max(self._capacity - 1, 1)
        for idx, series in enumerate(self._data):
            color = self._colors[idx % len(self._colors)]
            series = series[-self._capacity:]
            n = len(series)
            segment: list[float] = []
            for i, value in enumerate(series + [None]):       # sentinel flushes the last segment
                if value is None:
                    self._flush(segment, color)
                    segment = []
                    continue
                x = right - (n - 1 - i) * step
                y = bottom - (bottom - top) * min(max(value / y_max, 0.0), 1.0)
                segment += [x, y]
        for i, name in enumerate(self._legend):
            self.create_text(right - 4, top + 2 + i * 12, text=name, anchor="ne", font=font(8, "bold"),
                             fill=self._colors[i % len(self._colors)])

    def _flush(self, coords: list[float], color: str) -> None:
        if len(coords) >= 4:
            self.create_line(*coords, fill=color, width=2, joinstyle="round")
        elif len(coords) == 2:
            x, y = coords
            self.create_oval(x - 2, y - 2, x + 2, y + 2, fill=color, outline=color)
