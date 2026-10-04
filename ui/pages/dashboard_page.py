from __future__ import annotations

import tkinter as tk

from models.snapshot import SystemSnapshot
from ui.pages.base import BasePage, unavailable_text
from ui.widgets.chart_card import ChartCard
from ui.widgets.metric_card import MetricCard
from utils.formatters import format_bytes, format_frequency, format_speed

_LAYOUT = (("cpu", "CPU", 0, 0), ("ram", "RAM", 0, 1), ("gpu", "GPU", 0, 2),
           ("disk", "Disk", 1, 0), ("network", "Network", 1, 1), ("temperature", "Temperature", 1, 2))


class DashboardPage(BasePage):
    title = "Dashboard"

    def build(self) -> None:
        body = tk.Frame(self, bg=self.p.bg)
        body.pack(fill="both", expand=True, padx=20, pady=16)
        self.header(body, "Dashboard", "Live overview of your system")
        grid = tk.Frame(body, bg=self.p.bg)
        grid.pack(fill="x")
        self.grid_uniform(grid, 3)
        self.cards: dict[str, MetricCard] = {}
        for key, title, row, col in _LAYOUT:
            card = MetricCard(grid, self.p, title, lines=2, show_bar=key not in ("network", "temperature"))
            card.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)
            self.cards[key] = card
        charts = tk.Frame(body, bg=self.p.bg)
        charts.pack(fill="both", expand=True, pady=(10, 0))
        self.grid_uniform(charts, 2)
        charts.grid_rowconfigure(0, weight=1)
        self.usage_chart = ChartCard(charts, self.p, "CPU & RAM usage", legend=["CPU", "RAM"])
        self.net_chart = ChartCard(charts, self.p, "Network throughput", y_max=None,
                                   y_formatter=format_speed, legend=["Download", "Upload"])
        self.usage_chart.grid(row=0, column=0, sticky="nsew", padx=6)
        self.net_chart.grid(row=0, column=1, sticky="nsew", padx=6)

    def update_view(self, snap: SystemSnapshot) -> None:
        ctx, cards = self.ctx, self.cards
        visible = ctx.settings.visible_metrics
        for key, card in cards.items():
            if visible.get(key, True):
                card.grid()
            else:
                card.grid_remove()

        cpu = snap.cpu
        if cpu:
            cards["cpu"].update_card(f"{cpu.usage_percent:.0f}%", [
                f"{format_frequency(cpu.current_frequency_mhz)} · {ctx.temp(cpu.package_temperature_celsius or cpu.temperature_celsius)}",
                f"{cpu.physical_cores or '?'} cores / {cpu.logical_processors} logical"],
                cpu.usage_percent, ctx.usage_color(cpu.usage_percent))
        else:
            cards["cpu"].update_card("N/A", [unavailable_text(snap, "cpu")])

        mem = snap.memory
        if mem:
            cards["ram"].update_card(f"{mem.percent:.0f}%", [
                f"{format_bytes(mem.used)} / {format_bytes(mem.total)}",
                f"Available {format_bytes(mem.available)}"], mem.percent, ctx.usage_color(mem.percent))
        else:
            cards["ram"].update_card("N/A", [unavailable_text(snap, "memory")])

        gpu = snap.gpu.gpus[0] if snap.gpu and snap.gpu.gpus else None
        if gpu:
            vram = (f"VRAM {format_bytes(gpu.vram_used)} / {format_bytes(gpu.vram_total)}"
                    if gpu.vram_used is not None else gpu.name)
            value = "N/A" if gpu.usage_percent is None else f"{gpu.usage_percent:.0f}%"
            cards["gpu"].update_card(value, [vram, ctx.temp(gpu.temperature_celsius)],
                                     gpu.usage_percent, ctx.usage_color(gpu.usage_percent))
        else:
            cards["gpu"].update_card("N/A", ["GPU information unavailable"])

        disk = snap.disk
        if disk and disk.partitions:
            main = disk.partitions[0]
            cards["disk"].update_card(f"{main.percent:.0f}%", [
                f"{main.mountpoint} {format_bytes(main.used)} / {format_bytes(main.total)}",
                f"R {format_speed(disk.total_read_speed)}   W {format_speed(disk.total_write_speed)}"],
                main.percent, ctx.usage_color(main.percent))
        else:
            cards["disk"].update_card("N/A", [unavailable_text(snap, "disk")])

        net = snap.network
        if net:
            cards["network"].update_card(f"↓ {format_speed(net.total_download_speed)}", [
                f"↑ {format_speed(net.total_upload_speed)}",
                f"Total ↓ {format_bytes(net.total_bytes_recv)}  ↑ {format_bytes(net.total_bytes_sent)}"])
        else:
            cards["network"].update_card("N/A", [unavailable_text(snap, "network")])

        cpu_t = (cpu.package_temperature_celsius or cpu.temperature_celsius) if cpu else None
        gpu_t = gpu.temperature_celsius if gpu else None
        known = [t for t in (cpu_t, gpu_t) if t is not None]
        if known:
            hottest = max(known)
            cards["temperature"].update_card(ctx.temp(hottest), [f"CPU {ctx.temp(cpu_t)}", f"GPU {ctx.temp(gpu_t)}"],
                                             color=ctx.temp_color(hottest))
        else:
            cards["temperature"].update_card("N/A", ["No temperature sensor detected",
                                                     "See the System page for details"])

        span, cap = ctx.axis()
        h = ctx.history
        self.usage_chart.draw([h.get("cpu.usage"), h.get("mem.usage")], span, cap)
        self.net_chart.draw([h.get("net.down"), h.get("net.up")], span, cap)
