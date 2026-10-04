"""Page base class and the shared context handed to every page."""
from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass

from config.settings import Settings, SettingsStore
from core.monitoring_service import MonitoringService
from models.snapshot import SystemSnapshot
from services.hardware_service import HistoryStore
from ui.styles.theme import Palette
from ui.widgets.common import font
from utils.formatters import format_temperature
from utils.levels import classify


@dataclass
class PageContext:
    palette: Palette
    store: SettingsStore
    history: HistoryStore
    service: MonitoringService

    @property
    def settings(self) -> Settings:
        return self.store.settings

    def usage_color(self, percent: float | None) -> str:
        return self.palette.color_for(classify(percent, self.settings.usage_thresholds))

    def temp_color(self, celsius: float | None) -> str:
        return self.palette.color_for(classify(celsius, self.settings.temp_thresholds_c))

    def temp(self, celsius: float | None) -> str:
        return format_temperature(celsius, self.settings.temperature_unit)

    def axis(self) -> tuple[float, int]:
        return float(self.settings.history_seconds), self.settings.history_points


def unavailable_text(snap: SystemSnapshot, key: str, default: str = "Not available") -> str:
    status = snap.statuses.get(key)
    if status is None:
        return default
    return status.message or status.state.value


class BasePage(tk.Frame):
    """A page owns its widgets (created once) and refreshes them in ``update_view``."""
    title = ""

    def __init__(self, parent: tk.Misc, ctx: PageContext) -> None:
        super().__init__(parent, bg=ctx.palette.bg)
        self.ctx = ctx
        self.p = ctx.palette
        self.build()

    def build(self) -> None:
        raise NotImplementedError

    def update_view(self, snap: SystemSnapshot) -> None:
        raise NotImplementedError

    def on_show(self) -> None:
        """Called when the page becomes visible."""

    def on_hide(self) -> None:
        """Called when the page is hidden."""

    # ---- small layout helpers --------------------------------------------------------
    def header(self, parent: tk.Misc, title: str, subtitle: str = "") -> tk.Label:
        tk.Label(parent, text=title, font=font(20, "bold"), fg=self.p.text, bg=self.p.bg,
                 anchor="w").pack(fill="x")
        sub = tk.Label(parent, text=subtitle, font=font(10), fg=self.p.muted, bg=self.p.bg, anchor="w",
                       justify="left")
        sub.pack(fill="x", pady=(0, 12))
        return sub

    def section(self, parent: tk.Misc, text: str, pady: tuple[int, int] = (16, 6)) -> tk.Label:
        label = tk.Label(parent, text=text, font=font(11, "bold"), fg=self.p.text, bg=self.p.bg, anchor="w")
        label.pack(fill="x", pady=pady)
        return label

    def grid_uniform(self, frame: tk.Frame, columns: int) -> None:
        for c in range(columns):
            frame.grid_columnconfigure(c, weight=1, uniform=f"c{id(frame)}")
