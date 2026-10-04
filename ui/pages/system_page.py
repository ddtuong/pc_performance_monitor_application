from __future__ import annotations

import tkinter as tk

from models.sensor import SensorKind, SensorReading
from models.snapshot import SystemSnapshot
from ui.pages.base import BasePage
from ui.widgets.common import font, set_text
from ui.widgets.info_grid import InfoGrid
from ui.widgets.table import Column, TableView
from utils.formatters import NA, format_bytes, format_duration, format_frequency, format_power, format_rpm
from utils.time_utils import format_datetime, uptime_seconds

_KEYS = ["Operating system", "Version", "Build", "Hostname", "Manufacturer", "Model", "BIOS",
         "Architecture", "Python", "Boot time", "Uptime"]
_COMPONENTS = ("cpu", "memory", "gpu", "disk", "network", "sensors", "processes", "system")


class SystemPage(BasePage):
    title = "System"

    def build(self) -> None:
        body = tk.Frame(self, bg=self.p.bg)
        body.pack(fill="both", expand=True, padx=20, pady=16)
        self.header(body, "System", "Machine details, collector health and detected sensors")
        self.info = InfoGrid(body, self.p, _KEYS, columns=2, value_wrap=300)
        self.info.pack(fill="x")
        self.section(body, "Collector health")
        self.health = TableView(body, self.p, [Column("c", "Component", 120), Column("s", "Status", 160),
                                               Column("d", "Details", 520, stretch=True)], height=7)
        self.health.pack(fill="x")
        self.section(body, "Detected sensors")
        self.sensor_note = tk.Label(body, text="", font=font(9), fg=self.p.muted, bg=self.p.bg, anchor="w",
                                    justify="left", wraplength=900)
        self.sensor_note.pack(fill="x", pady=(0, 6))
        self.sensors = TableView(body, self.p, [Column("hw", "Hardware", 200), Column("name", "Sensor", 220),
                                                Column("type", "Type", 90), Column("val", "Value", 110, "e")],
                                 height=10)
        self.sensors.pack(fill="both", expand=True)

    def _value(self, r: SensorReading) -> str:
        if r.kind == SensorKind.TEMPERATURE:
            return self.ctx.temp(r.value)
        if r.kind == SensorKind.FAN:
            return format_rpm(r.value)
        if r.kind == SensorKind.POWER:
            return format_power(r.value)
        if r.kind == SensorKind.CLOCK:
            return format_frequency(r.value)
        if r.kind == SensorKind.DATA:
            return format_bytes(r.value * (1024 ** 2 if r.unit == "MB" else 1024 ** 3))
        return f"{r.value:.1f} {r.unit}"

    def update_view(self, snap: SystemSnapshot) -> None:
        s = snap.system
        i = self.info
        if s:
            i.set("Operating system", s.os_name); i.set("Version", s.os_version)
            i.set("Build", s.os_build or NA); i.set("Hostname", s.hostname)
            i.set("Manufacturer", s.manufacturer or NA); i.set("Model", s.model or NA)
            i.set("BIOS", s.bios or NA); i.set("Architecture", s.architecture)
            i.set("Python", s.python_version); i.set("Boot time", format_datetime(s.boot_time))
            i.set("Uptime", format_duration(uptime_seconds(s.boot_time)))
        self.health.set_rows([(k, (k.title(), snap.statuses[k].state.value, snap.statuses[k].message or "OK"))
                              for k in _COMPONENTS if k in snap.statuses])
        readings = sorted(snap.sensors.readings, key=lambda r: (r.hardware_type, r.hardware_name, r.kind.value, r.name)) \
            if snap.sensors else []
        if readings:
            set_text(self.sensor_note, "Sources: " + ", ".join(snap.sensors.sources))
        else:
            set_text(self.sensor_note, "No sensors detected. On Windows, run LibreHardwareMonitor and "
                                       "`pip install wmi` to expose CPU/GPU/SSD temperatures, fans and power.")
        self.sensors.set_rows([(f"s{n}", (r.hardware_name or r.hardware_type, r.name, r.kind.value, self._value(r)))
                               for n, r in enumerate(readings[:400])])
