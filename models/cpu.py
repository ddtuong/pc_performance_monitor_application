from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LogicalProcessorInfo:
    """One logical processor (a hardware thread, what Windows calls a 'logical processor')."""
    index: int
    usage_percent: float
    frequency_mhz: Optional[float] = None   # None when the OS cannot report it per processor


@dataclass(frozen=True)
class PhysicalCoreInfo:
    """A physical core and the logical processors that belong to it."""
    index: int
    logical_indices: tuple[int, ...]
    efficiency_class: Optional[int] = None  # Windows hybrid CPUs: higher = performance core


@dataclass
class CPUInfo:
    name: str
    manufacturer: str
    architecture: str
    physical_cores: Optional[int]
    logical_processors: int
    usage_percent: float
    current_frequency_mhz: Optional[float] = None
    base_frequency_mhz: Optional[float] = None
    max_frequency_mhz: Optional[float] = None
    temperature_celsius: Optional[float] = None
    package_temperature_celsius: Optional[float] = None
    power_watts: Optional[float] = None
    load_average: Optional[tuple[float, float, float]] = None
    logical_processors_info: list[LogicalProcessorInfo] = field(default_factory=list)
    # None = topology unknown. Never guessed.
    topology: Optional[list[PhysicalCoreInfo]] = None

    @property
    def threads_per_core(self) -> Optional[float]:
        if not self.physical_cores:
            return None
        return self.logical_processors / self.physical_cores
