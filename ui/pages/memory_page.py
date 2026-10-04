from __future__ import annotations

import tkinter as tk

from models.snapshot import SystemSnapshot
from ui.pages.base import BasePage, unavailable_text
from ui.widgets.chart_card import ChartCard
from ui.widgets.info_grid import InfoGrid
from ui.widgets.progress_card import ProgressCard
from utils.formatters import NA, format_bytes, format_percentage


class MemoryPage(BasePage):
    title = "Memory"

    def build(self) -> None:
        body = tk.Frame(self, bg=self.p.bg)
        body.pack(fill="both", expand=True, padx=20, pady=16)
        self.sub = self.header(body, "Memory", "Physical memory and swap / page file")
        row = tk.Frame(body, bg=self.p.bg)
        row.pack(fill="x")
        self.grid_uniform(row, 2)
        self.ram_card = ProgressCard(row, self.p, "RAM")
        self.swap_card = ProgressCard(row, self.p, "Swap / page file")
        self.ram_card.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        self.swap_card.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)
        self.section(body, "Details")
        self.info = InfoGrid(body, self.p, ["Total", "Used", "Available", "Free", "Cached", "Usage",
                                            "Swap total", "Swap used", "Swap free", "Swap usage"], columns=2)
        self.info.pack(fill="x", padx=6)
        self.section(body, "History")
        self.chart = ChartCard(body, self.p, "RAM usage", height=170)
        self.chart.pack(fill="both", expand=True, padx=6)

    def update_view(self, snap: SystemSnapshot) -> None:
        mem, ctx = snap.memory, self.ctx
        if mem is None:
            self.sub.configure(text=f"Memory information unavailable: {unavailable_text(snap, 'memory')}")
            return
        self.ram_card.update_card(f"{format_bytes(mem.used)} / {format_bytes(mem.total)}", mem.percent,
                                  ctx.usage_color(mem.percent), f"Available {format_bytes(mem.available)}")
        if mem.swap_total:
            self.swap_card.update_card(f"{format_bytes(mem.swap_used)} / {format_bytes(mem.swap_total)}",
                                       mem.swap_percent, ctx.usage_color(mem.swap_percent),
                                       f"Free {format_bytes(mem.swap_free)}")
        else:
            self.swap_card.update_card("No swap configured", None, None)
        i = self.info
        i.set("Total", format_bytes(mem.total)); i.set("Used", format_bytes(mem.used))
        i.set("Available", format_bytes(mem.available)); i.set("Free", format_bytes(mem.free))
        i.set("Cached", format_bytes(mem.cached) if mem.cached is not None else f"{NA} (not reported by this OS)")
        i.set("Usage", format_percentage(mem.percent, 1), ctx.usage_color(mem.percent))
        i.set("Swap total", format_bytes(mem.swap_total)); i.set("Swap used", format_bytes(mem.swap_used))
        i.set("Swap free", format_bytes(mem.swap_free)); i.set("Swap usage", format_percentage(mem.swap_percent, 1))
        span, cap = ctx.axis()
        self.chart.draw([ctx.history.get("mem.usage")], span, cap)
