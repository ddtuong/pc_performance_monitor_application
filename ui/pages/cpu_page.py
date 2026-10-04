from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional

from models.cpu import CPUInfo
from models.snapshot import SystemSnapshot
from ui.pages.base import BasePage, unavailable_text
from ui.widgets.chart_card import ChartCard
from ui.widgets.common import font, set_text
from ui.widgets.cpu_core_card import CPUCoreCard
from ui.widgets.metric_card import MetricCard
from ui.widgets.scrollable import ScrollableFrame
from utils.formatters import NA, format_frequency, format_power

_MIN_TILE_WIDTH = 150


class CPUPage(BasePage):
    title = "CPU"

    def build(self) -> None:
        scroll = ScrollableFrame(self, self.p.bg)
        scroll.pack(fill="both", expand=True)
        body = tk.Frame(scroll.body, bg=self.p.bg)
        body.pack(fill="both", expand=True, padx=20, pady=16)

        self.name_label = self.header(body, "CPU", "Detecting processor...")
        stats = tk.Frame(body, bg=self.p.bg)
        stats.pack(fill="x")
        self.grid_uniform(stats, 3)
        self.cards: dict[str, MetricCard] = {}
        for n, (key, title) in enumerate((("usage", "Usage"), ("freq", "Frequency"), ("cores", "Cores"),
                                          ("temp", "Temperature"), ("power", "Power"), ("load", "Load average"))):
            card = MetricCard(stats, self.p, title, lines=2, show_bar=key == "usage")
            card.grid(row=n // 3, column=n % 3, sticky="nsew", padx=6, pady=6)
            self.cards[key] = card

        self.section(body, "History")
        charts = tk.Frame(body, bg=self.p.bg)
        charts.pack(fill="x")
        self.grid_uniform(charts, 2)
        self.usage_chart = ChartCard(charts, self.p, "Overall CPU usage", height=140)
        self.freq_chart = ChartCard(charts, self.p, "CPU frequency", height=140, y_max=None,
                                    y_formatter=format_frequency)
        self.temp_chart = ChartCard(charts, self.p, "CPU temperature", height=140, y_max=None,
                                    y_formatter=lambda v: self.ctx.temp(v))
        self.per_chart = ChartCard(charts, self.p, "Per logical processor usage", height=140)
        for n, chart in enumerate((self.usage_chart, self.freq_chart, self.temp_chart, self.per_chart)):
            chart.grid(row=n // 2, column=n % 2, sticky="nsew", padx=6, pady=6)

        self.section(body, "Logical processors")
        self.core_note = tk.Label(
            body, anchor="w", justify="left", font=font(9), fg=self.p.muted, bg=self.p.bg, wraplength=900,
            text="Each tile is one logical processor (hardware thread). Physical cores and logical "
                 "processors are different: with SMT/Hyper-Threading one core exposes two logical processors.")
        self.core_note.pack(fill="x", pady=(0, 6))
        self.tiles_frame = tk.Frame(body, bg=self.p.bg)
        self.tiles_frame.pack(fill="x")
        self.tiles: list[CPUCoreCard] = []
        self._cols = 0
        self.tiles_frame.bind("<Configure>", lambda _e: self._relayout())

        self.section(body, "Core / thread topology")
        self.topo_note = tk.Label(body, text="", anchor="w", justify="left", font=font(9),
                                  fg=self.p.muted, bg=self.p.bg, wraplength=900)
        self.topo_note.pack(fill="x", pady=(0, 6))
        tree_wrap = tk.Frame(body, bg=self.p.surface, highlightbackground=self.p.border, highlightthickness=1)
        tree_wrap.pack(fill="x", pady=(0, 10))
        self.tree = ttk.Treeview(tree_wrap, columns=("usage", "freq"), style="App.Treeview", height=12)
        self.tree.heading("#0", text="Processor", anchor="w")
        self.tree.heading("usage", text="Usage", anchor="e")
        self.tree.heading("freq", text="Frequency", anchor="e")
        self.tree.column("#0", width=260, stretch=True)
        self.tree.column("usage", width=100, anchor="e", stretch=False)
        self.tree.column("freq", width=120, anchor="e", stretch=False)
        tree_scroll = ttk.Scrollbar(tree_wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side="left", fill="x", expand=True)
        tree_scroll.pack(side="right", fill="y")
        self._tree_signature: Optional[tuple] = None
        self._tree_cache: dict[tuple[str, str], str] = {}

    # ---- layout ----------------------------------------------------------------------
    def _relayout(self) -> None:
        width = self.tiles_frame.winfo_width()
        cols = max(2, min(8, width // _MIN_TILE_WIDTH)) if width > 1 else max(self._cols, 4)
        if cols == self._cols and all(t.winfo_manager() for t in self.tiles):
            return
        for c in range(max(self._cols, cols)):
            self.tiles_frame.grid_columnconfigure(c, weight=1 if c < cols else 0, uniform="tile" if c < cols else "")
        for i, tile in enumerate(self.tiles):
            tile.grid(row=i // cols, column=i % cols, sticky="nsew", padx=4, pady=4)
        self._cols = cols

    def _sync_tiles(self, count: int) -> None:
        """Create/remove tiles only when the logical-processor count changes."""
        if count == len(self.tiles):
            return
        while len(self.tiles) < count:
            self.tiles.append(CPUCoreCard(self.tiles_frame, self.p, len(self.tiles)))
        while len(self.tiles) > count:
            self.tiles.pop().destroy()
        self._cols = 0
        self._relayout()

    # ---- topology tree ---------------------------------------------------------------
    def _rebuild_tree(self, cpu: CPUInfo) -> None:
        signature = (len(cpu.logical_processors_info), tuple(cpu.topology or ()))
        if signature == self._tree_signature:
            return
        self._tree_signature = signature
        self._tree_cache.clear()
        self.tree.delete(*self.tree.get_children())
        if cpu.topology:
            classes = {c.efficiency_class for c in cpu.topology if c.efficiency_class is not None}
            top = max(classes) if len(classes) > 1 else None
            for core in cpu.topology:
                kind = ""
                if top is not None:
                    kind = " (performance)" if core.efficiency_class == top else " (efficiency)"
                self.tree.insert("", "end", iid=f"core{core.index}", open=True,
                                 text=f"Physical Core {core.index}{kind}")
                for idx in core.logical_indices:
                    self.tree.insert(f"core{core.index}", "end", iid=f"lp{idx}", text=f"Logical Processor {idx}")
            self.topo_note.configure(text="Topology reported by the operating system.")
        else:
            for lp in cpu.logical_processors_info:
                self.tree.insert("", "end", iid=f"lp{lp.index}", text=f"Logical Processor {lp.index}")
            self.topo_note.configure(text="Physical-core mapping is not exposed (or failed validation) on this "
                                          "system, so only logical processors are shown. Nothing is guessed.")
        self.tree.configure(height=min(18, max(4, len(self.tree.get_children()) +
                                               (cpu.logical_processors if cpu.topology else 0))))

    def _set_cell(self, iid: str, column: str, text: str) -> None:
        if self._tree_cache.get((iid, column)) != text:
            self._tree_cache[(iid, column)] = text
            self.tree.set(iid, column, text)

    # ---- update ----------------------------------------------------------------------
    def update_view(self, snap: SystemSnapshot) -> None:
        cpu, ctx = snap.cpu, self.ctx
        if cpu is None:
            set_text(self.name_label, f"CPU information unavailable: {unavailable_text(snap, 'cpu')}")
            return
        set_text(self.name_label, f"{cpu.name}\n{cpu.manufacturer} · {cpu.architecture}")
        usage_color = ctx.usage_color(cpu.usage_percent)
        cards = self.cards
        cards["usage"].update_card(f"{cpu.usage_percent:.0f}%", ["Overall"], cpu.usage_percent, usage_color)
        cards["freq"].update_card(format_frequency(cpu.current_frequency_mhz), [
            f"Base {format_frequency(cpu.base_frequency_mhz)}", f"Max {format_frequency(cpu.max_frequency_mhz)}"])
        tpc = cpu.threads_per_core
        cards["cores"].update_card(f"{cpu.physical_cores or NA} / {cpu.logical_processors}", [
            "Physical cores / Logical processors",
            f"{tpc:.0f} threads per core" if tpc and tpc == int(tpc) else "Threads per core: N/A"])
        temp = cpu.package_temperature_celsius if cpu.package_temperature_celsius is not None else cpu.temperature_celsius
        cards["temp"].update_card(ctx.temp(temp), [
            f"Package {ctx.temp(cpu.package_temperature_celsius)}",
            "" if temp is not None else "Needs a sensor provider"], color=ctx.temp_color(temp))
        cards["power"].update_card(format_power(cpu.power_watts), [
            "" if cpu.power_watts is not None else "Needs a sensor provider"])
        la = cpu.load_average
        cards["load"].update_card(f"{la[0]:.2f}" if la else NA,
                                  [f"5m {la[1]:.2f} · 15m {la[2]:.2f}" if la else ""])

        # tiles
        lps = cpu.logical_processors_info
        self._sync_tiles(len(lps))
        any_freq = any(lp.frequency_mhz is not None for lp in lps)
        for tile, lp in zip(self.tiles, lps):
            tile.update_card(lp.usage_percent, format_frequency(lp.frequency_mhz) if any_freq else "",
                             ctx.usage_color(lp.usage_percent))
        extra = "" if any_freq else " Per-processor frequency is not exposed by this OS/API, so it is not shown."
        set_text(self.core_note, "Each tile is one logical processor (hardware thread). Physical cores and "
                 "logical processors are different: with SMT/Hyper-Threading one core exposes two." + extra)

        # tree
        self._rebuild_tree(cpu)
        by_index = {lp.index: lp for lp in lps}
        if cpu.topology:
            for core in cpu.topology:
                members = [by_index[i] for i in core.logical_indices if i in by_index]
                if members:
                    avg = sum(m.usage_percent for m in members) / len(members)
                    self._set_cell(f"core{core.index}", "usage", f"{avg:.0f}%")
        for lp in lps:
            self._set_cell(f"lp{lp.index}", "usage", f"{lp.usage_percent:.0f}%")
            self._set_cell(f"lp{lp.index}", "freq", format_frequency(lp.frequency_mhz) if any_freq else NA)

        # charts
        span, cap = ctx.axis()
        h = ctx.history
        self.usage_chart.draw([h.get("cpu.usage")], span, cap)
        self.freq_chart.draw([h.get("cpu.freq")], span, cap, "N/A")
        self.temp_chart.draw([h.get("cpu.temp")], span, cap, "N/A - no sensor provider")
        self.per_chart.draw(h.prefix("cpu.core."), span, cap)
