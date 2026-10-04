from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PartitionInfo:
    device: str
    mountpoint: str
    fstype: str
    total: int
    used: int
    free: int
    percent: float


@dataclass
class DiskIOInfo:
    """I/O statistics of one physical disk. Speeds are deltas, not counters."""
    name: str
    read_bytes: int
    write_bytes: int
    read_count: int
    write_count: int
    read_speed: Optional[float] = None          # bytes/s (None on first sample)
    write_speed: Optional[float] = None
    read_ops_per_s: Optional[float] = None
    write_ops_per_s: Optional[float] = None


@dataclass
class DiskInfo:
    partitions: list[PartitionInfo] = field(default_factory=list)
    io: list[DiskIOInfo] = field(default_factory=list)
    total_read_speed: Optional[float] = None
    total_write_speed: Optional[float] = None
    io_available: bool = True
