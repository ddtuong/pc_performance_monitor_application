"""Process collector (Task-Manager style)."""
from __future__ import annotations

from typing import Optional

import psutil

from collectors.base import BaseCollector
from models.process import ProcessesInfo, ProcessInfo
from utils.logger import get_logger

log = get_logger(__name__)
_FAST_ATTRS = ["pid", "name", "cpu_percent", "memory_percent", "memory_info", "num_threads", "status"]


class ProcessCollector(BaseCollector[ProcessesInfo]):
    """``psutil.process_iter`` caches Process objects, so ``cpu_percent`` is a true delta
    between calls. Username/exe are slow to query, so they are fetched once per PID."""
    name = "processes"

    def __init__(self) -> None:
        self._cpus = psutil.cpu_count(logical=True) or 1
        self._static: dict[int, tuple[float, Optional[str], Optional[str]]] = {}
        psutil.cpu_percent()
        for p in psutil.process_iter(["cpu_percent"]):   # prime per-process CPU baselines
            pass

    def _static_info(self, proc: psutil.Process) -> tuple[Optional[str], Optional[str]]:
        try:
            created = proc.create_time()
        except (psutil.Error, OSError):
            created = 0.0
        cached = self._static.get(proc.pid)
        if cached and cached[0] == created:           # same PID reused? created differs
            return cached[1], cached[2]
        try:
            user: Optional[str] = proc.username()
        except (psutil.Error, OSError, KeyError):
            user = None
        try:
            exe: Optional[str] = proc.exe() or None
        except (psutil.Error, OSError):
            exe = None
        self._static[proc.pid] = (created, user, exe)
        return user, exe

    def collect(self) -> ProcessesInfo:
        out: list[ProcessInfo] = []
        total_threads = 0
        live: set[int] = set()
        for proc in psutil.process_iter(_FAST_ATTRS, ad_value=None):
            info = proc.info
            live.add(info["pid"])
            mem = info.get("memory_info")
            threads = info.get("num_threads") or 0
            total_threads += threads
            user, exe = self._static_info(proc)
            out.append(ProcessInfo(
                pid=info["pid"], name=info.get("name") or "?",
                cpu_percent=min(100.0, (info.get("cpu_percent") or 0.0) / self._cpus),
                memory_percent=info.get("memory_percent") or 0.0,
                memory_bytes=mem.rss if mem else 0, threads=threads,
                status=info.get("status") or "?", username=user, executable=exe))
        for pid in [p for p in self._static if p not in live]:
            del self._static[pid]
        return ProcessesInfo(out, total_threads)
