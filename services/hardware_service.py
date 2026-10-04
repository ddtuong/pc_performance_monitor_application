"""HardwareService: turns snapshots into bounded history series for the charts."""
from __future__ import annotations

from collections import deque
from typing import Deque, Optional

from models.snapshot import SystemSnapshot

Series = Deque[Optional[float]]


class HistoryStore:
    """Named bounded series. ``None`` entries are gaps (metric unavailable)."""

    def __init__(self, maxlen: int) -> None:
        self._maxlen = maxlen
        self._series: dict[str, Series] = {}

    def resize(self, maxlen: int) -> None:
        self._maxlen = maxlen
        for key, old in list(self._series.items()):
            self._series[key] = deque(old, maxlen=maxlen)

    def append(self, key: str, value: Optional[float]) -> None:
        series = self._series.get(key)
        if series is None:
            series = self._series[key] = deque(maxlen=self._maxlen)
        series.append(value)

    def get(self, key: str) -> list[Optional[float]]:
        return list(self._series.get(key, ()))

    def prefix(self, prefix: str) -> list[list[Optional[float]]]:
        keys = sorted((k for k in self._series if k.startswith(prefix)),
                      key=lambda k: int(k.rsplit(".", 1)[1]) if k.rsplit(".", 1)[1].isdigit() else 0)
        return [self.get(k) for k in keys]


class HardwareService:
    def __init__(self, history_points: int) -> None:
        self.history = HistoryStore(history_points)
        self.latest: Optional[SystemSnapshot] = None

    def set_history_points(self, points: int) -> None:
        self.history.resize(points)

    def update(self, snap: SystemSnapshot) -> None:
        self.latest = snap
        h = self.history
        cpu = snap.cpu
        h.append("cpu.usage", cpu.usage_percent if cpu else None)
        h.append("cpu.freq", cpu.current_frequency_mhz if cpu else None)
        h.append("cpu.temp", (cpu.package_temperature_celsius or cpu.temperature_celsius) if cpu else None)
        if cpu:
            for lp in cpu.logical_processors_info:
                h.append(f"cpu.core.{lp.index}", lp.usage_percent)
        h.append("mem.usage", snap.memory.percent if snap.memory else None)
        gpu = snap.gpu.gpus[0] if snap.gpu and snap.gpu.gpus else None
        h.append("gpu.usage", gpu.usage_percent if gpu else None)
        h.append("gpu.temp", gpu.temperature_celsius if gpu else None)
        h.append("disk.read", snap.disk.total_read_speed if snap.disk else None)
        h.append("disk.write", snap.disk.total_write_speed if snap.disk else None)
        h.append("net.down", snap.network.total_download_speed if snap.network else None)
        h.append("net.up", snap.network.total_upload_speed if snap.network else None)
