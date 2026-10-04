"""Hardware sensor abstraction (temperatures, fans, power, GPU/storage sensors).

Windows exposes almost no sensors without a kernel driver. The practical, open source
route is LibreHardwareMonitor (or OpenHardwareMonitor) running in the background, which
publishes sensors over WMI. Providers are detected dynamically; missing ones are
reported, never faked.
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Optional

import psutil

from collectors.base import BaseCollector
from core.exceptions import ApiUnavailable, CollectorError, NotSupported
from models.sensor import SensorKind, SensorReading, SensorsInfo
from utils.logger import get_logger

log = get_logger(__name__)
RETRY_AFTER_S = 30.0


class SensorProvider(ABC):
    name = "provider"

    @abstractmethod
    def collect(self) -> list[SensorReading]:
        """Return readings or raise CollectorError."""

    def close(self) -> None:
        pass


# --------------------------------------------------------------------- psutil (Linux/macOS)
_PSUTIL_HW = {
    "coretemp": "Cpu", "k10temp": "Cpu", "zenpower": "Cpu", "cpu_thermal": "Cpu",
    "cpu-thermal": "Cpu", "acpitz": "Motherboard", "nvme": "Storage", "drivetemp": "Storage",
    "amdgpu": "GpuAmd", "radeon": "GpuAmd", "nouveau": "GpuNvidia", "i915": "GpuIntel",
}


class PsutilSensorProvider(SensorProvider):
    name = "psutil"

    def collect(self) -> list[SensorReading]:
        if not hasattr(psutil, "sensors_temperatures"):
            raise NotSupported("psutil exposes no sensors on this OS")
        out: list[SensorReading] = []
        for chip, entries in (psutil.sensors_temperatures() or {}).items():
            hw = _PSUTIL_HW.get(chip, chip)
            for e in entries:
                if e.current is not None:
                    out.append(SensorReading(e.label or chip, SensorKind.TEMPERATURE, float(e.current),
                                             "°C", hw, chip, self.name))
        for chip, entries in (getattr(psutil, "sensors_fans", lambda: {})() or {}).items():
            for e in entries:
                out.append(SensorReading(e.label or chip, SensorKind.FAN, float(e.current),
                                         "RPM", _PSUTIL_HW.get(chip, chip), chip, self.name))
        if not out:
            raise NotSupported("No sensors reported by the OS")
        return out


# --------------------------------------------------------------------- LibreHardwareMonitor
_NAMESPACES = ("root\\LibreHardwareMonitor", "root\\OpenHardwareMonitor")
_ID_TO_HW = (
    ("intelcpu", "Cpu"), ("amdcpu", "Cpu"), ("cpu", "Cpu"),
    ("gpu-nvidia", "GpuNvidia"), ("nvidiagpu", "GpuNvidia"),
    ("gpu-amd", "GpuAmd"), ("atigpu", "GpuAmd"), ("amdgpu", "GpuAmd"),
    ("gpu-intel", "GpuIntel"), ("intelgpu", "GpuIntel"),
    ("nvme", "Storage"), ("hdd", "Storage"), ("ssd", "Storage"), ("storage", "Storage"),
    ("mainboard", "Motherboard"), ("lpc", "Motherboard"), ("motherboard", "Motherboard"),
    ("ram", "Memory"), ("memory", "Memory"),
)
_KIND = {
    "Temperature": (SensorKind.TEMPERATURE, "°C"), "Fan": (SensorKind.FAN, "RPM"),
    "Power": (SensorKind.POWER, "W"), "Clock": (SensorKind.CLOCK, "MHz"),
    "Load": (SensorKind.LOAD, "%"), "Data": (SensorKind.DATA, "GB"),
    "SmallData": (SensorKind.DATA, "MB"),
}


def hardware_type_from_identifier(identifier: str) -> str:
    first = identifier.strip("/").split("/")[0].lower()
    for prefix, hw in _ID_TO_HW:
        if first.startswith(prefix):
            return hw
    return first or "Unknown"


class LibreHardwareMonitorProvider(SensorProvider):
    """Reads sensors published over WMI by LibreHardwareMonitor / OpenHardwareMonitor."""
    name = "LibreHardwareMonitor"

    def __init__(self) -> None:
        self._conn = None
        self._hw_names: dict[str, str] = {}
        self._com_initialised = False

    def _connect(self) -> None:
        try:
            import pythoncom  # type: ignore
            import wmi  # type: ignore
        except ImportError:
            raise ApiUnavailable("Optional 'wmi' package not installed (pip install wmi)")
        if not self._com_initialised:
            pythoncom.CoInitialize()  # COM is per-thread: must run on the worker thread
            self._com_initialised = True
        last: Exception | None = None
        for ns in _NAMESPACES:
            try:
                conn = wmi.WMI(namespace=ns)
                self._hw_names = {h.Identifier: h.Name for h in conn.Hardware()}
                self._conn = conn
                log.info("Connected to sensor provider %s", ns)
                return
            except Exception as exc:  # wmi raises x_wmi / com_error
                last = exc
        raise ApiUnavailable("LibreHardwareMonitor is not running (WMI namespace not found)") from last

    def collect(self) -> list[SensorReading]:
        if self._conn is None:
            self._connect()
        try:
            out: list[SensorReading] = []
            for s in self._conn.Sensor():
                kind = _KIND.get(s.SensorType)
                if kind is None or s.Value is None:
                    continue
                out.append(SensorReading(
                    name=s.Name, kind=kind[0], value=float(s.Value), unit=kind[1],
                    hardware_type=hardware_type_from_identifier(s.Identifier),
                    hardware_name=self._hw_names.get(s.Parent, ""), source=self.name))
            return out
        except Exception as exc:
            self._conn = None  # force reconnect next time
            raise ApiUnavailable(f"Sensor query failed: {exc}") from exc

    def close(self) -> None:
        if self._com_initialised:
            try:
                import pythoncom  # type: ignore
                pythoncom.CoUninitialize()
            except Exception:
                pass
            self._com_initialised = False
        self._conn = None


class SensorCollector(BaseCollector[SensorsInfo]):
    """Aggregates providers. ``latest`` lets CPU/GPU collectors reuse the same readings."""
    name = "sensors"

    def __init__(self, providers: Optional[list[SensorProvider]] = None) -> None:
        self._providers = providers if providers is not None else [
            LibreHardwareMonitorProvider(), PsutilSensorProvider()]
        self._retry_at: dict[str, float] = {}
        self.latest: Optional[SensorsInfo] = None

    def collect(self) -> SensorsInfo:
        self.latest = None
        readings: list[SensorReading] = []
        sources: list[str] = []
        problems: list[str] = []
        now = time.monotonic()
        for provider in self._providers:
            if self._retry_at.get(provider.name, 0) > now:
                continue
            try:
                got = provider.collect()
                if got:
                    readings.extend(got)
                    sources.append(provider.name)
            except CollectorError as exc:
                problems.append(f"{provider.name}: {exc}")
                self._retry_at[provider.name] = now + RETRY_AFTER_S
                log.info("Sensor provider %s unavailable: %s", provider.name, exc)
            except Exception as exc:
                problems.append(f"{provider.name}: {exc}")
                self._retry_at[provider.name] = now + RETRY_AFTER_S
                log.exception("Sensor provider %s failed", provider.name)
        if not readings:
            raise ApiUnavailable("; ".join(problems) or "No sensor providers are active")
        self.latest = SensorsInfo(readings, sources)
        return self.latest

    def shutdown(self) -> None:
        for provider in self._providers:
            provider.close()
