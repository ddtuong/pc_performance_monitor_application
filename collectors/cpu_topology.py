"""Physical-core -> logical-processor mapping.

Only reports a mapping when the OS provides it AND it passes validation.
Returns ``None`` otherwise: topology is never guessed.
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path
from typing import Optional

from models.cpu import PhysicalCoreInfo
from utils.logger import get_logger

log = get_logger(__name__)


def validate_topology(cores: list[PhysicalCoreInfo], logical_count: int) -> bool:
    """Every logical processor must appear exactly once."""
    seen: list[int] = []
    for core in cores:
        seen.extend(core.logical_indices)
    return sorted(seen) == list(range(logical_count))


def read_topology(logical_count: int) -> Optional[list[PhysicalCoreInfo]]:
    try:
        if sys.platform == "win32":
            cores = _windows_topology()
        elif sys.platform.startswith("linux"):
            cores = _linux_topology(Path("/sys/devices/system/cpu"), logical_count)
        else:
            return None
    except Exception as exc:  # topology is optional; never break CPU monitoring
        log.warning("CPU topology unavailable: %s", exc)
        return None
    if cores and validate_topology(cores, logical_count):
        return cores
    log.info("CPU topology missing or failed validation; showing logical processors only")
    return None


def _linux_topology(base: Path, logical_count: int) -> list[PhysicalCoreInfo]:
    groups: dict[tuple[str, str], list[int]] = {}
    for i in range(logical_count):
        topo = base / f"cpu{i}" / "topology"
        core_id = (topo / "core_id").read_text().strip()
        package = (topo / "physical_package_id").read_text().strip()
        groups.setdefault((package, core_id), []).append(i)
    ordered = sorted(groups.items(), key=lambda kv: min(kv[1]))
    return [PhysicalCoreInfo(index=n, logical_indices=tuple(sorted(v)))
            for n, (_, v) in enumerate(ordered)]


def parse_core_records(buffer: bytes) -> list[PhysicalCoreInfo]:
    """Parse SYSTEM_LOGICAL_PROCESSOR_INFORMATION_EX records (RelationProcessorCore, x64).

    Record layout: Relationship(4) Size(4) Flags(1) EfficiencyClass(1) Reserved(20)
    GroupCount(2) then GROUP_AFFINITY[GroupCount] {Mask(8) Group(2) Reserved(6)}.
    Only processor group 0 is supported (<= 64 logical processors); otherwise the
    mapping is considered unreliable and an empty list is returned.
    """
    cores: list[PhysicalCoreInfo] = []
    offset = 0
    while offset + 8 <= len(buffer):
        relationship, size = struct.unpack_from("<II", buffer, offset)
        if size == 0:
            break
        if relationship == 0:  # RelationProcessorCore
            efficiency = buffer[offset + 9]
            (group_count,) = struct.unpack_from("<H", buffer, offset + 30)
            indices: list[int] = []
            for g in range(group_count):
                mask, group = struct.unpack_from("<QH", buffer, offset + 32 + g * 16)
                if group != 0:
                    return []
                indices.extend(b for b in range(64) if mask >> b & 1)
            cores.append(PhysicalCoreInfo(len(cores), tuple(sorted(indices)), efficiency))
        offset += size
    return cores


def _windows_topology() -> list[PhysicalCoreInfo]:
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    func = kernel32.GetLogicalProcessorInformationEx
    func.argtypes = [wintypes.DWORD, ctypes.c_void_p, ctypes.POINTER(wintypes.DWORD)]
    func.restype = wintypes.BOOL
    length = wintypes.DWORD(0)
    func(0, None, ctypes.byref(length))  # RelationProcessorCore: query required size
    if length.value == 0:
        return []
    buf = ctypes.create_string_buffer(length.value)
    if not func(0, buf, ctypes.byref(length)):
        raise OSError(ctypes.get_last_error(), "GetLogicalProcessorInformationEx failed")
    return parse_core_records(buf.raw[: length.value])
