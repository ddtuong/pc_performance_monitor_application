from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class MemoryInfo:
    total: int
    used: int
    available: int
    free: int
    percent: float
    cached: Optional[int]          # not exposed on every OS (psutil gives none on Windows)
    swap_total: int
    swap_used: int
    swap_free: int
    swap_percent: float
