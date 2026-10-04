from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class SensorKind(str, Enum):
    TEMPERATURE = "Temperature"
    FAN = "Fan"
    POWER = "Power"
    LOAD = "Load"
    CLOCK = "Clock"
    DATA = "Data"
    OTHER = "Other"


@dataclass(frozen=True)
class SensorReading:
    """One real reading from a hardware sensor provider."""
    name: str                      # e.g. "CPU Package"
    kind: SensorKind
    value: float
    unit: str                      # "°C", "RPM", "W", ...
    hardware_type: str = ""        # e.g. "Cpu", "GpuNvidia", "Storage", "Motherboard"
    hardware_name: str = ""
    source: str = ""               # provider name


@dataclass
class SensorsInfo:
    readings: list[SensorReading] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)

    def find(self, kind: SensorKind, hardware_type: str | None = None,
             name_contains: tuple[str, ...] = ()) -> list[SensorReading]:
        out = []
        for r in self.readings:
            if r.kind != kind:
                continue
            if hardware_type and hardware_type.lower() not in r.hardware_type.lower():
                continue
            if name_contains and not any(s.lower() in r.name.lower() for s in name_contains):
                continue
            out.append(r)
        return out

    def first_value(self, kind: SensorKind, hardware_type: str | None = None,
                    name_contains: tuple[str, ...] = ()) -> Optional[float]:
        """Return the first match, trying each name pattern in priority order."""
        if not name_contains:
            found = self.find(kind, hardware_type)
            return found[0].value if found else None
        for pattern in name_contains:
            found = self.find(kind, hardware_type, (pattern,))
            if found:
                return found[0].value
        return None
