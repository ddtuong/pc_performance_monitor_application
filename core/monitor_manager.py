"""MonitorManager: owns the collectors and builds one SystemSnapshot per cycle.

A failing collector never aborts a cycle: its section becomes None and its status
records why (state + message), while the technical error is logged.
"""
from __future__ import annotations

import logging
import time
from typing import Callable, Optional

from collectors.base import BaseCollector
from collectors.cpu import CPUCollector
from collectors.disk import DiskCollector
from collectors.gpu import GPUCollector
from collectors.memory import MemoryCollector
from collectors.network import NetworkCollector
from collectors.processes import ProcessCollector
from collectors.sensors import SensorCollector
from collectors.system import SystemCollector
from config.constants import MIN_PROCESS_INTERVAL_S
from core.exceptions import CollectorError
from models.snapshot import CollectorStatus, MetricState, SystemSnapshot

log = logging.getLogger(__name__)

# snapshot attribute -> collector key. Order matters: sensors run first so that
# CPU/GPU collectors can reuse SensorCollector.latest.
SECTION_ORDER = ("sensors", "system", "cpu", "memory", "gpu", "disk", "network", "processes")


class MonitorManager:
    def __init__(self, collectors: dict[str, BaseCollector], clock: Callable[[], float] = time.monotonic) -> None:
        self._collectors = collectors
        self._clock = clock
        self.processes_enabled = False          # toggled by the UI (only when the page is visible)
        self._last_process_time = float("-inf")
        self._last_processes = None

    @classmethod
    def create_default(cls) -> "MonitorManager":
        sensors = SensorCollector()
        return cls({
            "sensors": sensors, "system": SystemCollector(), "cpu": CPUCollector(sensors),
            "memory": MemoryCollector(), "gpu": GPUCollector(sensors), "disk": DiskCollector(),
            "network": NetworkCollector(), "processes": _LazyProcessCollector(),
        })

    def collect_all(self, force_processes: bool = False) -> SystemSnapshot:
        snapshot = SystemSnapshot()
        for key in SECTION_ORDER:
            collector = self._collectors.get(key)
            if collector is None:
                continue
            if key == "processes" and not self._should_collect_processes(force_processes):
                snapshot.processes = self._last_processes
                continue
            try:
                value = collector.collect()
                setattr(snapshot, key, value)
                snapshot.statuses[key] = CollectorStatus(MetricState.AVAILABLE)
                if key == "processes":
                    self._last_processes = value
                    self._last_process_time = self._clock()
            except CollectorError as exc:
                snapshot.statuses[key] = CollectorStatus(exc.state, str(exc))
                log.info("Collector '%s' unavailable: %s", key, exc)
            except Exception as exc:  # never let one collector crash the loop
                snapshot.statuses[key] = CollectorStatus(MetricState.UNAVAILABLE, "Unexpected error (see log)")
                log.exception("Collector '%s' failed: %s", key, exc)
        return snapshot

    def _should_collect_processes(self, force: bool) -> bool:
        if not self.processes_enabled:
            return False
        return force or self._clock() - self._last_process_time >= MIN_PROCESS_INTERVAL_S

    def shutdown(self) -> None:
        for key, collector in self._collectors.items():
            try:
                collector.shutdown()
            except Exception:
                log.exception("Shutdown failed for '%s'", key)


class _LazyProcessCollector(BaseCollector):
    """Build the ProcessCollector on first use (its priming pass is not free)."""
    name = "processes"

    def __init__(self) -> None:
        self._inner: Optional[ProcessCollector] = None

    def collect(self):
        if self._inner is None:
            self._inner = ProcessCollector()
        return self._inner.collect()
