"""Disk collector: partition capacity plus per-disk I/O speeds computed from deltas."""
from __future__ import annotations

from typing import Optional

import psutil

from collectors.base import BaseCollector
from models.disk import DiskInfo, DiskIOInfo, PartitionInfo
from utils.logger import get_logger
from utils.rates import RateTracker

log = get_logger(__name__)


class DiskCollector(BaseCollector[DiskInfo]):
    name = "disk"

    def __init__(self, rates: Optional[RateTracker] = None) -> None:
        self._rates = rates or RateTracker()

    def collect_partitions(self) -> list[PartitionInfo]:
        out: list[PartitionInfo] = []
        for part in psutil.disk_partitions(all=False):
            if "cdrom" in part.opts or not part.fstype:
                continue
            try:
                usage = psutil.disk_usage(part.mountpoint)
            except (PermissionError, OSError) as exc:   # e.g. empty card reader
                log.debug("Skipping %s: %s", part.mountpoint, exc)
                continue
            out.append(PartitionInfo(part.device, part.mountpoint, part.fstype,
                                     usage.total, usage.used, usage.free, float(usage.percent)))
        return out

    def collect_io(self) -> Optional[list[DiskIOInfo]]:
        try:
            counters = psutil.disk_io_counters(perdisk=True)
        except Exception as exc:
            log.warning("Disk I/O counters unavailable: %s", exc)
            return None
        if not counters:
            return None
        live = set()
        out: list[DiskIOInfo] = []
        for name, c in counters.items():
            keys = [(name, k) for k in ("r", "w", "rc", "wc")]
            live.update(keys)
            out.append(DiskIOInfo(
                name=name, read_bytes=c.read_bytes, write_bytes=c.write_bytes,
                read_count=c.read_count, write_count=c.write_count,
                read_speed=self._rates.update(keys[0], c.read_bytes),
                write_speed=self._rates.update(keys[1], c.write_bytes),
                read_ops_per_s=self._rates.update(keys[2], c.read_count),
                write_ops_per_s=self._rates.update(keys[3], c.write_count),
            ))
        self._rates.forget_missing(live)
        return sorted(out, key=lambda d: d.name)

    def collect(self) -> DiskInfo:
        io = self.collect_io()
        info = DiskInfo(partitions=self.collect_partitions(), io=io or [], io_available=io is not None)
        reads = [d.read_speed for d in info.io if d.read_speed is not None]
        writes = [d.write_speed for d in info.io if d.write_speed is not None]
        info.total_read_speed = sum(reads) if reads else None
        info.total_write_speed = sum(writes) if writes else None
        return info
