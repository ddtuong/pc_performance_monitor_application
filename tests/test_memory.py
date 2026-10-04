from collections import namedtuple
from unittest.mock import patch

from collectors import memory as memory_module
from collectors.memory import MemoryCollector

VM = namedtuple("VM", "total available percent used free")
VMC = namedtuple("VMC", "total available percent used free cached")
SW = namedtuple("SW", "total used free percent sin sout")


def test_memory_collect_without_cached_field():
    with patch.object(memory_module.psutil, "virtual_memory", return_value=VM(16000, 6000, 62.5, 10000, 2000)), \
         patch.object(memory_module.psutil, "swap_memory", return_value=SW(8000, 1000, 7000, 12.5, 0, 0)):
        info = MemoryCollector().collect()
    assert info.total == 16000 and info.percent == 62.5
    assert info.cached is None                      # Windows: not reported, not invented
    assert info.swap_total == 8000 and info.swap_percent == 12.5


def test_memory_collect_with_cached_field():
    with patch.object(memory_module.psutil, "virtual_memory", return_value=VMC(100, 50, 50.0, 50, 10, 7)), \
         patch.object(memory_module.psutil, "swap_memory", return_value=SW(0, 0, 0, 0.0, 0, 0)):
        info = MemoryCollector().collect()
    assert info.cached == 7 and info.swap_total == 0
