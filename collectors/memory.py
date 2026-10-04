from __future__ import annotations

import psutil

from collectors.base import BaseCollector
from models.memory import MemoryInfo


class MemoryCollector(BaseCollector[MemoryInfo]):
    name = "memory"

    def collect(self) -> MemoryInfo:
        vm = psutil.virtual_memory()
        sw = psutil.swap_memory()
        cached = getattr(vm, "cached", None)    # absent on Windows
        return MemoryInfo(
            total=vm.total, used=vm.used, available=vm.available, free=vm.free,
            percent=float(vm.percent), cached=cached,
            swap_total=sw.total, swap_used=sw.used, swap_free=sw.free,
            swap_percent=float(sw.percent),
        )
