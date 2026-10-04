from __future__ import annotations

import tkinter as tk

from models.sensor import SensorKind
from models.snapshot import SystemSnapshot
from ui.pages.base import BasePage, unavailable_text
from ui.widgets.chart_card import ChartCard
from ui.widgets.common import font, set_text
from ui.widgets.metric_card import MetricCard
from ui.widgets.table import Column, TableView
from utils.formatters import format_bytes, format_count, format_speed


class DiskPage(BasePage):
    title = "Disk"

    def build(self) -> None:
        body = tk.Frame(self, bg=self.p.bg)
        body.pack(fill="both", expand=True, padx=20, pady=16)
        self.sub = self.header(body, "Disk", "Capacity, throughput and operations")
        row = tk.Frame(body, bg=self.p.bg)
        row.pack(fill="x")
        self.grid_uniform(row, 2)
        self.read_card = MetricCard(row, self.p, "Read speed", lines=1, show_bar=False)
        self.write_card = MetricCard(row, self.p, "Write speed", lines=1, show_bar=False)
        self.read_card.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        self.write_card.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)

        self.section(body, "Volumes")
        self.parts = TableView(body, self.p, [
            Column("device", "Device", 140), Column("mount", "Mount point", 110), Column("fs", "FS", 60),
            Column("total", "Capacity", 90, "e"), Column("used", "Used", 90, "e"),
            Column("free", "Free", 90, "e"), Column("pct", "Usage", 70, "e")], height=5)
        self.parts.pack(fill="x")
        self.section(body, "Physical disk I/O")
        self.io_note = tk.Label(body, text="", font=font(9), fg=self.p.muted, bg=self.p.bg, anchor="w")
        self.io_note.pack(fill="x")
        self.io = TableView(body, self.p, [
            Column("disk", "Disk", 130), Column("rs", "Read speed", 100, "e"), Column("ws", "Write speed", 100, "e"),
            Column("riops", "Read IOPS", 90, "e"), Column("wiops", "Write IOPS", 90, "e"),
            Column("rops", "Read ops (total)", 120, "e"), Column("wops", "Write ops (total)", 120, "e")], height=5)
        self.io.pack(fill="x")
        self.section(body, "Storage temperature / SMART")
        self.temp_note = tk.Label(body, text="", font=font(9), fg=self.p.muted, bg=self.p.bg, anchor="w",
                                  justify="left", wraplength=800)
        self.temp_note.pack(fill="x")
        self.temps = TableView(body, self.p, [Column("dev", "Device", 260), Column("sensor", "Sensor", 160),
                                              Column("val", "Value", 100, "e")], height=3)
        self.temps.pack(fill="x")
        self.section(body, "History")
        self.chart = ChartCard(body, self.p, "Total read / write", y_max=None, y_formatter=format_speed,
                               legend=["Read", "Write"])
        self.chart.pack(fill="both", expand=True)

    def update_view(self, snap: SystemSnapshot) -> None:
        disk, ctx = snap.disk, self.ctx
        if disk is None:
            set_text(self.sub, f"Disk information unavailable: {unavailable_text(snap, 'disk')}")
            return
        self.read_card.update_card(format_speed(disk.total_read_speed), ["All physical disks"])
        self.write_card.update_card(format_speed(disk.total_write_speed), ["All physical disks"])
        self.parts.set_rows([(p.mountpoint, (p.device, p.mountpoint, p.fstype, format_bytes(p.total),
                                             format_bytes(p.used), format_bytes(p.free), f"{p.percent:.0f}%"))
                             for p in disk.partitions])
        set_text(self.io_note, "" if disk.io_available else
                 "I/O counters unavailable (on Windows try running 'diskperf -y' as administrator).")
        self.io.set_rows([(d.name, (d.name, format_speed(d.read_speed), format_speed(d.write_speed),
                                    format_count(d.read_ops_per_s), format_count(d.write_ops_per_s),
                                    format_count(d.read_count), format_count(d.write_count))) for d in disk.io])
        readings = snap.sensors.find(SensorKind.TEMPERATURE, "Storage") if snap.sensors else []
        set_text(self.temp_note, "" if readings else
                 "N/A - drive temperatures need a sensor provider (LibreHardwareMonitor). Not faked.")
        self.temps.set_rows([(f"t{i}", (r.hardware_name or r.hardware_type, r.name, ctx.temp(r.value)))
                             for i, r in enumerate(readings)])
        span, cap = ctx.axis()
        h = ctx.history
        self.chart.draw([h.get("disk.read"), h.get("disk.write")], span, cap)
