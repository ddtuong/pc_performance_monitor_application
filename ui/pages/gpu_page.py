from __future__ import annotations

import tkinter as tk

from models.gpu import GPUInfo
from models.snapshot import SystemSnapshot
from ui.pages.base import BasePage, PageContext, unavailable_text
from ui.widgets.chart_card import ChartCard
from ui.widgets.common import font, set_text
from ui.widgets.info_grid import InfoGrid
from ui.widgets.progress_card import ProgressCard
from utils.formatters import NA, format_bytes, format_frequency, format_power, format_rpm


class GPUPanel(tk.Frame):
    """Everything about one GPU. Created once per detected GPU."""

    def __init__(self, parent: tk.Misc, ctx: PageContext) -> None:
        p = ctx.palette
        super().__init__(parent, bg=p.bg)
        self.ctx = ctx
        self.name = tk.Label(self, font=font(13, "bold"), fg=p.text, bg=p.bg, anchor="w")
        self.name.pack(fill="x", pady=(8, 6))
        row = tk.Frame(self, bg=p.bg)
        row.pack(fill="x")
        for c in range(2):
            row.grid_columnconfigure(c, weight=1, uniform="gpu")
        self.usage = ProgressCard(row, p, "GPU usage")
        self.vram = ProgressCard(row, p, "VRAM")
        self.usage.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.vram.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        self.info = InfoGrid(self, p, ["Temperature", "Core clock", "Memory clock", "Fan speed", "Power",
                                       "Vendor", "Data source"], columns=2)
        self.info.pack(fill="x", pady=(10, 0))
        self.note = tk.Label(self, font=font(9), fg=p.muted, bg=p.bg, anchor="w", justify="left", wraplength=800)
        self.note.pack(fill="x", pady=(6, 0))

    def update_gpu(self, g: GPUInfo) -> None:
        ctx = self.ctx
        set_text(self.name, g.name)
        usage = g.usage_percent
        self.usage.update_card("N/A" if usage is None else f"{usage:.0f}%", usage, ctx.usage_color(usage))
        vp = g.vram_percent
        if g.vram_total and g.vram_used is not None:
            self.vram.update_card(f"{format_bytes(g.vram_used)} / {format_bytes(g.vram_total)}", vp, ctx.usage_color(vp))
        else:
            total = f"Total {format_bytes(g.vram_total)}" if g.vram_total else ""
            self.vram.update_card("N/A", None, None, total)
        fan = f"{g.fan_percent:.0f}%" if g.fan_percent is not None else format_rpm(g.fan_rpm)
        i = self.info
        i.set("Temperature", ctx.temp(g.temperature_celsius), ctx.temp_color(g.temperature_celsius) if g.temperature_celsius is not None else None)
        i.set("Core clock", format_frequency(g.core_clock_mhz))
        i.set("Memory clock", format_frequency(g.memory_clock_mhz))
        i.set("Fan speed", fan)
        i.set("Power", format_power(g.power_watts))
        i.set("Vendor", g.vendor)
        i.set("Data source", g.source)
        set_text(self.note, g.note)


class GPUPage(BasePage):
    title = "GPU"

    def build(self) -> None:
        body = tk.Frame(self, bg=self.p.bg)
        body.pack(fill="both", expand=True, padx=20, pady=16)
        self.sub = self.header(body, "GPU", "Graphics adapters")
        self.empty = tk.Label(body, text="GPU information unavailable", font=font(14, "bold"),
                              fg=self.p.muted, bg=self.p.bg)
        self.detail = tk.Label(body, text="", font=font(9), fg=self.p.muted, bg=self.p.bg,
                               wraplength=800, justify="left")
        self.panels_frame = tk.Frame(body, bg=self.p.bg)
        self.panels: list[GPUPanel] = []
        self._signature: tuple = ()
        charts = tk.Frame(body, bg=self.p.bg)
        self.charts = charts
        self.grid_uniform(charts, 2)
        self.usage_chart = ChartCard(charts, self.p, "GPU usage (first GPU)")
        self.temp_chart = ChartCard(charts, self.p, "GPU temperature (first GPU)", y_max=None,
                                    y_formatter=lambda v: self.ctx.temp(v))
        self.usage_chart.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.temp_chart.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

    def _show_empty(self, message: str) -> None:
        self.panels_frame.pack_forget()
        self.charts.pack_forget()
        self.empty.pack(pady=(40, 6))
        self.detail.pack()
        set_text(self.detail, message)

    def update_view(self, snap: SystemSnapshot) -> None:
        gpus = snap.gpu.gpus if snap.gpu else []
        if not gpus:
            self._show_empty(unavailable_text(snap, "gpu", "No GPU detected"))
            return
        self.empty.pack_forget()
        self.detail.pack_forget()
        self.panels_frame.pack(fill="x")
        self.charts.pack(fill="both", expand=True, pady=(14, 0))
        signature = tuple(g.name for g in gpus)
        if signature != self._signature:            # rebuild panels only if the GPU set changed
            for panel in self.panels:
                panel.destroy()
            self.panels = [GPUPanel(self.panels_frame, self.ctx) for _ in gpus]
            for panel in self.panels:
                panel.pack(fill="x")
            self._signature = signature
        for panel, gpu in zip(self.panels, gpus):
            panel.update_gpu(gpu)
        span, cap = self.ctx.axis()
        h = self.ctx.history
        self.usage_chart.draw([h.get("gpu.usage")], span, cap, "N/A")
        self.temp_chart.draw([h.get("gpu.temp")], span, cap, "N/A")
