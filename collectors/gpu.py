"""GPU collector built on a provider abstraction.

GPUCollector -> [NvidiaProvider (NVML), SensorGPUProvider (AMD/Intel via sensors),
                 WindowsAdapterProvider (names/VRAM only, no live metrics)]
Providers raise CollectorError when they cannot work; values that are not reported are None.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Optional

from collectors.base import BaseCollector
from collectors.sensors import SensorCollector
from core.exceptions import ApiUnavailable, HardwareNotDetected
from models.gpu import GPUInfo, GPUsInfo
from models.sensor import SensorKind
from utils.logger import get_logger
from utils.platform_utils import IS_WINDOWS

log = get_logger(__name__)


def detect_vendor(name: str) -> str:
    n = name.lower()
    if "nvidia" in n or "geforce" in n or "quadro" in n or "rtx" in n:
        return "NVIDIA"
    if "amd" in n or "radeon" in n or "ati " in n:
        return "AMD"
    if "intel" in n or "arc" in n.split():
        return "Intel"
    return "Unknown"


class GPUProvider(ABC):
    name = "provider"

    @abstractmethod
    def collect(self) -> list[GPUInfo]:
        """Return GPUs or raise CollectorError."""

    def close(self) -> None:
        pass


class NvidiaProvider(GPUProvider):
    """NVIDIA via NVML (package ``nvidia-ml-py``, imported as ``pynvml``)."""
    name = "NVML"

    def __init__(self) -> None:
        self._nvml: Any = None
        self._handles: list[Any] = []
        self._failure: Optional[str] = None
        self._initialised = False

    def _init(self) -> None:
        if self._initialised:
            return
        if self._failure:
            raise ApiUnavailable(self._failure)
        try:
            import pynvml  # type: ignore
        except ImportError:
            self._failure = "NVML not installed (pip install nvidia-ml-py)"
            raise ApiUnavailable(self._failure)
        try:
            pynvml.nvmlInit()
            count = pynvml.nvmlDeviceGetCount()
        except pynvml.NVMLError as exc:
            self._failure = f"NVIDIA driver/NVML unavailable: {exc}"
            raise ApiUnavailable(self._failure)
        if count == 0:
            self._failure = "No NVIDIA GPU detected"
            raise HardwareNotDetected(self._failure)
        self._nvml = pynvml
        self._handles = [pynvml.nvmlDeviceGetHandleByIndex(i) for i in range(count)]
        self._initialised = True

    def _safe(self, fn: Callable[..., Any], *args: Any) -> Any:
        try:
            return fn(*args)
        except self._nvml.NVMLError as exc:
            log.debug("NVML %s failed: %s", getattr(fn, "__name__", fn), exc)
            return None

    def collect(self) -> list[GPUInfo]:
        self._init()
        n = self._nvml
        out: list[GPUInfo] = []
        for h in self._handles:
            name = self._safe(n.nvmlDeviceGetName, h) or "NVIDIA GPU"
            if isinstance(name, bytes):
                name = name.decode(errors="replace")
            util = self._safe(n.nvmlDeviceGetUtilizationRates, h)
            mem = self._safe(n.nvmlDeviceGetMemoryInfo, h)
            power = self._safe(n.nvmlDeviceGetPowerUsage, h)
            out.append(GPUInfo(
                name=str(name), vendor="NVIDIA", source=self.name,
                usage_percent=float(util.gpu) if util else None,
                vram_used=int(mem.used) if mem else None,
                vram_total=int(mem.total) if mem else None,
                temperature_celsius=self._to_float(self._safe(n.nvmlDeviceGetTemperature, h, n.NVML_TEMPERATURE_GPU)),
                core_clock_mhz=self._to_float(self._safe(n.nvmlDeviceGetClockInfo, h, n.NVML_CLOCK_GRAPHICS)),
                memory_clock_mhz=self._to_float(self._safe(n.nvmlDeviceGetClockInfo, h, n.NVML_CLOCK_MEM)),
                fan_percent=self._to_float(self._safe(n.nvmlDeviceGetFanSpeed, h)),
                power_watts=power / 1000.0 if power is not None else None,
            ))
        return out

    @staticmethod
    def _to_float(v: Any) -> Optional[float]:
        return None if v is None else float(v)

    def close(self) -> None:
        if self._initialised:
            try:
                self._nvml.nvmlShutdown()
            except Exception:
                pass
            self._initialised = False


class SensorGPUProvider(GPUProvider):
    """AMD / Intel GPUs through the sensor layer (LibreHardwareMonitor or psutil)."""
    name = "Sensors"

    def __init__(self, sensors: SensorCollector) -> None:
        self._sensors = sensors

    def collect(self) -> list[GPUInfo]:
        info = self._sensors.latest
        if info is None:
            raise ApiUnavailable("No sensor provider active for AMD/Intel GPUs")
        names = {r.hardware_name or r.hardware_type for r in info.readings
                 if r.hardware_type.startswith("Gpu") and r.hardware_type != "GpuNvidia"}
        out: list[GPUInfo] = []
        for hw_name in sorted(names):
            mine = [r for r in info.readings if (r.hardware_name or r.hardware_type) == hw_name]
            hw_type = mine[0].hardware_type

            def pick(kind: SensorKind, *patterns: str) -> Optional[float]:
                for p in patterns:
                    for r in mine:
                        if r.kind == kind and p.lower() in r.name.lower():
                            return r.value
                return None

            used = pick(SensorKind.DATA, "GPU Memory Used", "D3D Dedicated Memory Used")
            total = pick(SensorKind.DATA, "GPU Memory Total", "D3D Dedicated Memory Total")
            unit_mb = any(r.kind == SensorKind.DATA and r.unit == "MB" for r in mine)
            scale = (1024 ** 2) if unit_mb else (1024 ** 3)
            vendor = {"GpuAmd": "AMD", "GpuIntel": "Intel"}.get(hw_type, detect_vendor(hw_name))
            out.append(GPUInfo(
                name=hw_name, vendor=vendor, source=self.name,
                usage_percent=pick(SensorKind.LOAD, "GPU Core", "GPU"),
                vram_used=int(used * scale) if used is not None else None,
                vram_total=int(total * scale) if total is not None else None,
                temperature_celsius=pick(SensorKind.TEMPERATURE, "GPU Core", "GPU Hotspot", "GPU"),
                core_clock_mhz=pick(SensorKind.CLOCK, "GPU Core"),
                memory_clock_mhz=pick(SensorKind.CLOCK, "GPU Memory"),
                fan_rpm=pick(SensorKind.FAN, "GPU Fan", "Fan"),
                power_watts=pick(SensorKind.POWER, "GPU Package", "GPU Core", "GPU"),
            ))
        if not out:
            raise HardwareNotDetected("No AMD/Intel GPU sensors found")
        return out


class WindowsAdapterProvider(GPUProvider):
    """Names + dedicated VRAM from the registry. NO live metrics (honestly reported as None)."""
    name = "Windows registry"
    _CLASS = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
    _SKIP = ("remote display", "basic render", "virtual")

    def __init__(self) -> None:
        self._cache: Optional[list[GPUInfo]] = None

    def collect(self) -> list[GPUInfo]:
        if not IS_WINDOWS:
            raise ApiUnavailable("Windows registry adapters only exist on Windows")
        if self._cache is None:
            self._cache = self._read()
        if not self._cache:
            raise HardwareNotDetected("No display adapter found in registry")
        return list(self._cache)

    def _read(self) -> list[GPUInfo]:
        import winreg
        out: list[GPUInfo] = []
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, self._CLASS) as root:
                i = 0
                while True:
                    try:
                        sub = winreg.EnumKey(root, i)
                    except OSError:
                        break
                    i += 1
                    if not sub.isdigit():
                        continue
                    try:
                        with winreg.OpenKey(root, sub) as key:
                            desc = str(winreg.QueryValueEx(key, "DriverDesc")[0])
                            if any(s in desc.lower() for s in self._SKIP):
                                continue
                            vram = None
                            try:
                                raw = winreg.QueryValueEx(key, "HardwareInformation.qwMemorySize")[0]
                                vram = int.from_bytes(raw, "little") if isinstance(raw, bytes) else int(raw)
                            except OSError:
                                pass
                            out.append(GPUInfo(
                                name=desc, vendor=detect_vendor(desc), source=self.name,
                                vram_total=vram or None,
                                note="Live metrics need NVML (NVIDIA) or LibreHardwareMonitor (AMD/Intel)."))
                    except OSError:
                        continue
        except OSError as exc:
            log.warning("Display adapter registry read failed: %s", exc)
        return out


class GPUCollector(BaseCollector[GPUsInfo]):
    name = "gpu"

    def __init__(self, sensors: Optional[SensorCollector] = None,
                 providers: Optional[list[GPUProvider]] = None) -> None:
        if providers is None:
            providers = [NvidiaProvider()]
            if sensors is not None:
                providers.append(SensorGPUProvider(sensors))
            providers.append(WindowsAdapterProvider())
        self._providers = providers

    def collect(self) -> GPUsInfo:
        gpus: list[GPUInfo] = []
        problems: list[str] = []
        for provider in self._providers:
            try:
                for g in provider.collect():
                    known = g.name.lower()
                    if not any(known in e.name.lower() or e.name.lower() in known for e in gpus):
                        gpus.append(g)
            except HardwareNotDetected as exc:
                problems.append(f"{provider.name}: {exc}")
            except ApiUnavailable as exc:
                problems.append(f"{provider.name}: {exc}")
            except Exception as exc:
                problems.append(f"{provider.name}: {exc}")
                log.exception("GPU provider %s failed", provider.name)
        if not gpus:
            raise HardwareNotDetected("; ".join(problems) or "No GPU detected")
        return GPUsInfo(gpus)

    def shutdown(self) -> None:
        for p in self._providers:
            p.close()
