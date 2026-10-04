from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GPUInfo:
    name: str
    vendor: str                                 # "NVIDIA" | "AMD" | "Intel" | "Unknown"
    source: str                                 # which provider produced the data
    usage_percent: Optional[float] = None
    vram_used: Optional[int] = None             # bytes
    vram_total: Optional[int] = None            # bytes
    temperature_celsius: Optional[float] = None
    core_clock_mhz: Optional[float] = None
    memory_clock_mhz: Optional[float] = None
    fan_percent: Optional[float] = None
    fan_rpm: Optional[float] = None
    power_watts: Optional[float] = None
    note: str = ""                              # e.g. why metrics are missing

    @property
    def vram_percent(self) -> Optional[float]:
        if self.vram_used is None or not self.vram_total:
            return None
        return self.vram_used * 100.0 / self.vram_total


@dataclass
class GPUsInfo:
    gpus: list[GPUInfo] = field(default_factory=list)
