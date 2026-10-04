"""The single object that travels from the worker thread to the UI."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from models.cpu import CPUInfo
from models.disk import DiskInfo
from models.gpu import GPUsInfo
from models.memory import MemoryInfo
from models.network import NetworkInfo
from models.process import ProcessesInfo
from models.sensor import SensorsInfo
from models.system import SystemInfo


class MetricState(str, Enum):
    AVAILABLE = "Available"
    UNAVAILABLE = "Unavailable"
    NOT_SUPPORTED = "Not supported"
    PERMISSION_DENIED = "Permission denied"
    HARDWARE_NOT_DETECTED = "Hardware not detected"
    API_UNAVAILABLE = "API unavailable"


@dataclass(frozen=True)
class CollectorStatus:
    state: MetricState = MetricState.AVAILABLE
    message: str = ""


@dataclass
class SystemSnapshot:
    timestamp: float = field(default_factory=time.time)
    cpu: Optional[CPUInfo] = None
    memory: Optional[MemoryInfo] = None
    gpu: Optional[GPUsInfo] = None
    disk: Optional[DiskInfo] = None
    network: Optional[NetworkInfo] = None
    sensors: Optional[SensorsInfo] = None
    processes: Optional[ProcessesInfo] = None
    system: Optional[SystemInfo] = None
    statuses: dict[str, CollectorStatus] = field(default_factory=dict)
