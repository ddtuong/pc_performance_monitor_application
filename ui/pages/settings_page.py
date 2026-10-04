from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from config.constants import HISTORY_CHOICES_S, INTERVAL_CHOICES_MS
from models.snapshot import SystemSnapshot
from ui.pages.base import BasePage
from ui.widgets.common import font

_METRICS = (("cpu", "CPU"), ("ram", "RAM"), ("gpu", "GPU"), ("disk", "Disk"),
            ("network", "Network"), ("temperature", "Temperature"))
_LEVELS = ("Moderate from", "High from", "Critical from")


def _label_for(mapping: dict[str, int], value: int) -> str:
    return next((k for k, v in mapping.items() if v == value), next(iter(mapping)))


class SettingsPage(BasePage):
    title = "Settings"

    def build(self) -> None:
        s = self.ctx.settings
        body = tk.Frame(self, bg=self.p.bg)
        body.pack(fill="both", expand=True, padx=20, pady=16)
        self.header(body, "Settings", "Changes apply immediately and are saved automatically")

        def row(label: str) -> tk.Frame:
            frame = tk.Frame(body, bg=self.p.bg)
            frame.pack(fill="x", pady=4)
            tk.Label(frame, text=label, width=24, anchor="w", font=font(10), fg=self.p.text,
                     bg=self.p.bg).pack(side="left")
            return frame

        self.interval = tk.StringVar(value=_label_for(INTERVAL_CHOICES_MS, s.interval_ms))
        self._combo(row("Monitoring interval"), self.interval, list(INTERVAL_CHOICES_MS),
                    lambda: self.ctx.store.update(interval_ms=INTERVAL_CHOICES_MS[self.interval.get()]))
        self.history = tk.StringVar(value=_label_for(HISTORY_CHOICES_S, s.history_seconds))
        self._combo(row("Chart history"), self.history, list(HISTORY_CHOICES_S),
                    lambda: self.ctx.store.update(history_seconds=HISTORY_CHOICES_S[self.history.get()]))
        self.theme = tk.StringVar(value=s.theme)
        self._combo(row("Theme"), self.theme, ["dark", "light"], lambda: self.ctx.store.update(theme=self.theme.get()))
        self.unit = tk.StringVar(value=s.temperature_unit)
        unit_row = row("Temperature unit")
        for text, val in (("Celsius (°C)", "C"), ("Fahrenheit (°F)", "F")):
            ttk.Radiobutton(unit_row, text=text, value=val, variable=self.unit,
                            command=lambda: self.ctx.store.update(temperature_unit=self.unit.get())).pack(side="left", padx=(0, 12))

        self.section(body, "Startup & logging")
        self._check(body, "Start with Windows (Windows only)", "start_with_windows", s.start_with_windows)
        self._check(body, "Start minimized", "start_minimized", s.start_minimized)
        self._check(body, "Enable logging (logs/app.log)", "enable_logging", s.enable_logging)
        self.log_level = tk.StringVar(value=s.log_level)
        self._combo(row("Log level"), self.log_level, ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                    lambda: self.ctx.store.update(log_level=self.log_level.get()))

        self.section(body, "Visible dashboard metrics")
        metrics = tk.Frame(body, bg=self.p.bg)
        metrics.pack(fill="x")
        self._metric_vars: dict[str, tk.BooleanVar] = {}
        for n, (key, label) in enumerate(_METRICS):
            var = tk.BooleanVar(value=s.visible_metrics.get(key, True))
            self._metric_vars[key] = var
            ttk.Checkbutton(metrics, text=label, variable=var, command=self._save_metrics).grid(
                row=n // 3, column=n % 3, sticky="w", padx=(0, 24), pady=2)

        self.section(body, "Colour thresholds")
        tk.Label(body, anchor="w", justify="left", wraplength=800, font=font(9), fg=self.p.muted, bg=self.p.bg,
                 text="Safe temperatures differ between CPU and GPU models. The temperature defaults below are "
                      "generic, not hardware limits: check your processor's/GPU's specification and adjust.").pack(fill="x")
        self._usage_vars = self._thresholds(body, "Usage (%)", s.usage_thresholds, self._save_usage)
        self._temp_vars = self._thresholds(body, "Temperature (°C)", s.temp_thresholds_c, self._save_temp)

    # ---- builders --------------------------------------------------------------------
    def _combo(self, parent: tk.Misc, var: tk.StringVar, values: list[str], on_change) -> None:
        box = ttk.Combobox(parent, textvariable=var, values=values, state="readonly", width=16)
        box.pack(side="left")
        box.bind("<<ComboboxSelected>>", lambda _e: on_change())

    def _check(self, parent: tk.Misc, text: str, key: str, value: bool) -> None:
        var = tk.BooleanVar(value=value)
        ttk.Checkbutton(parent, text=text, variable=var,
                        command=lambda: self.ctx.store.update(**{key: var.get()})).pack(anchor="w", pady=2)

    def _thresholds(self, parent: tk.Misc, title: str, values, on_change) -> list[tk.StringVar]:
        frame = tk.Frame(parent, bg=self.p.bg)
        frame.pack(fill="x", pady=4)
        tk.Label(frame, text=title, width=24, anchor="w", font=font(10), fg=self.p.text, bg=self.p.bg).pack(side="left")
        vars_: list[tk.StringVar] = []
        for label, value in zip(_LEVELS, values):
            tk.Label(frame, text=label, font=font(9), fg=self.p.muted, bg=self.p.bg).pack(side="left", padx=(0, 4))
            var = tk.StringVar(value=f"{value:g}")
            box = ttk.Spinbox(frame, from_=0, to=200, increment=1, width=5, textvariable=var, command=on_change)
            box.pack(side="left", padx=(0, 14))
            box.bind("<Return>", lambda _e: on_change())
            box.bind("<FocusOut>", lambda _e: on_change())
            vars_.append(var)
        return vars_

    # ---- save handlers ---------------------------------------------------------------
    def _save_metrics(self) -> None:
        self.ctx.store.update(visible_metrics={k: v.get() for k, v in self._metric_vars.items()})

    @staticmethod
    def _read(vars_: list[tk.StringVar]) -> tuple[float, float, float] | None:
        try:
            a, b, c = (float(v.get()) for v in vars_)
        except ValueError:
            return None
        return (a, b, c) if 0 <= a < b < c else None

    def _save_usage(self) -> None:
        if (t := self._read(self._usage_vars)):
            self.ctx.store.update(usage_thresholds=t)

    def _save_temp(self) -> None:
        if (t := self._read(self._temp_vars)):
            self.ctx.store.update(temp_thresholds_c=t)

    def update_view(self, snap: SystemSnapshot) -> None:
        pass   # settings do not depend on live data
