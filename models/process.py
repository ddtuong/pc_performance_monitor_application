from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ProcessInfo:
    pid: int
    name: str
    cpu_percent: float          # normalised to 0-100 of the whole machine (Task Manager style)
    memory_percent: float
    memory_bytes: int           # working set (RSS)
    threads: int
    status: str
    username: Optional[str] = None
    executable: Optional[str] = None


@dataclass
class ProcessesInfo:
    processes: list[ProcessInfo] = field(default_factory=list)
    total_threads: int = 0
