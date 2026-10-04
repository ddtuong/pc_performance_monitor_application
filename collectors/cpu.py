"""CPU collector: name, topology, usage, per-logical-processor usage, frequency, sensors."""
from __future__ import annotations

import platform
import re
import sys
from pathlib import Path
from typing import Optional

import psutil

from collectors.base import BaseCollector
from collectors.cpu_topology import read_topology
from collectors.sensors import SensorCollector
from models.cpu import CPUInfo, LogicalProcessorInfo
from models.sensor import SensorKind
from utils.logger import get_logger
from utils.platform_utils import IS_LINUX, IS_WINDOWS, read_registry_value

log = get_logger(__name__)
_CPU_KEY = r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
_PKG_NAMES = ("CPU Package", "Package", "Tdie", "Tctl")
_TEMP_NAMES = ("CPU Package", "Core Average", "Core Max", "Package", "Tdie", "Tctl", "Core")


def parse_vendor(vendor_id: Optional[str], name: str = "") -> str:
    text = f"{vendor_id or ''} {name}".lower()
    if "intel" in text:
        return "Intel"
    if "amd" in text or "authenticamd" in text:
        return "AMD"
    if "apple" in text:
        return "Apple"
    if "arm" in text or "qualcomm" in text:
        return "ARM"
    return vendor_id or "Unknown"


def _linux_cpuinfo(field: str) -> Optional[str]:
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.lower().startswith(field):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return None


def get_cpu_name() -> str:
    name = None
    if IS_WINDOWS:
        name = read_registry_value("HKEY_LOCAL_MACHINE", _CPU_KEY, "ProcessorNameString")
    elif IS_LINUX:
        name = _linux_cpuinfo("model name")
    name = name or platform.processor() or "Unknown CPU"
    return re.sub(r"\s+", " ", str(name)).strip()


def get_cpu_vendor(name: str) -> str:
    vendor = None
    if IS_WINDOWS:
        vendor = read_registry_value("HKEY_LOCAL_MACHINE", _CPU_KEY, "VendorIdentifier")
    elif IS_LINUX:
        vendor = _linux_cpuinfo("vendor_id")
    return parse_vendor(str(vendor) if vendor else None, name)


def get_cpu_architecture() -> str:
    return platform.machine() or "Unknown"


def get_base_frequency_mhz() -> Optional[float]:
    """Nominal (base) clock. Windows: registry '~MHz'. Linux: intel_pstate base_frequency."""
    if IS_WINDOWS:
        value = read_registry_value("HKEY_LOCAL_MACHINE", _CPU_KEY, "~MHz")
        return float(value) if value else None
    if IS_LINUX:
        try:
            khz = Path("/sys/devices/system/cpu/cpu0/cpufreq/base_frequency").read_text().strip()
            return float(khz) / 1000
        except (OSError, ValueError):
            return None
    return None


class CPUCollector(BaseCollector[CPUInfo]):
    """Collects CPU data. ``sensors`` (optional) supplies temperature and power."""
    name = "cpu"

    def __init__(self, sensors: Optional[SensorCollector] = None) -> None:
        self._sensors = sensors
        self._cpu_name = get_cpu_name()
        self._vendor = get_cpu_vendor(self._cpu_name)
        self._arch = get_cpu_architecture()
        self._logical = psutil.cpu_count(logical=True) or 1
        self._physical = psutil.cpu_count(logical=False)   # may be None
        self._base_mhz = get_base_frequency_mhz()
        self._topology = read_topology(self._logical)       # static: read once
        psutil.cpu_percent(percpu=True)                     # prime: first call is meaningless
        psutil.cpu_percent()

    # ---- small, individually testable pieces -------------------------------------------
    def get_cpu_usage(self) -> float:
        return float(psutil.cpu_percent())

    def get_per_processor_usage(self) -> list[float]:
        values = psutil.cpu_percent(percpu=True)
        return [float(v) for v in values]

    def get_frequencies(self) -> tuple[Optional[float], Optional[float], list[Optional[float]]]:
        """Return (current, max, per_logical) in MHz. Missing values are None."""
        try:
            overall = psutil.cpu_freq()
        except Exception as exc:
            log.debug("cpu_freq failed: %s", exc)
            overall = None
        current = float(overall.current) if overall and overall.current else None
        maximum = float(overall.max) if overall and overall.max else None
        per: list[Optional[float]] = [None] * self._logical
        try:
            listed = psutil.cpu_freq(percpu=True)
            if listed and len(listed) == self._logical:   # Windows returns one entry: ignore
                per = [float(f.current) if f.current else None for f in listed]
        except Exception as exc:
            log.debug("per-cpu frequency unavailable: %s", exc)
        return current, maximum, per

    def get_load_average(self) -> Optional[tuple[float, float, float]]:
        try:
            return tuple(float(x) for x in psutil.getloadavg())  # type: ignore[return-value]
        except (AttributeError, OSError):
            return None

    def _sensor_values(self) -> tuple[Optional[float], Optional[float], Optional[float]]:
        info = self._sensors.latest if self._sensors else None
        if info is None:
            return None, None, None
        package = info.first_value(SensorKind.TEMPERATURE, "Cpu", _PKG_NAMES)
        temp = info.first_value(SensorKind.TEMPERATURE, "Cpu", _TEMP_NAMES)
        if temp is None:
            temp = info.first_value(SensorKind.TEMPERATURE, "Cpu")
        power = info.first_value(SensorKind.POWER, "Cpu", ("CPU Package", "Package"))
        return temp, package, power

    # ---- public ---------------------------------------------------------------------
    def collect(self) -> CPUInfo:
        usage = self.get_cpu_usage()
        per_usage = self.get_per_processor_usage()
        current, maximum, per_freq = self.get_frequencies()
        temp, package, power = self._sensor_values()
        logical = [
            LogicalProcessorInfo(i, u, per_freq[i] if i < len(per_freq) else None)
            for i, u in enumerate(per_usage)
        ]
        return CPUInfo(
            name=self._cpu_name, manufacturer=self._vendor, architecture=self._arch,
            physical_cores=self._physical, logical_processors=self._logical,
            usage_percent=usage, current_frequency_mhz=current,
            base_frequency_mhz=self._base_mhz, max_frequency_mhz=maximum,
            temperature_celsius=temp, package_temperature_celsius=package, power_watts=power,
            load_average=self.get_load_average(), logical_processors_info=logical,
            topology=self._topology,
        )
