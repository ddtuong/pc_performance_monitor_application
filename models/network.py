from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NetworkInterfaceInfo:
    name: str
    is_up: bool
    speed_mbps: int
    ipv4: list[str]
    ipv6: list[str]
    mac: str
    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int
    errors_in: int
    errors_out: int
    dropped_in: int
    dropped_out: int
    download_speed: Optional[float] = None      # bytes/s
    upload_speed: Optional[float] = None


@dataclass
class NetworkInfo:
    interfaces: list[NetworkInterfaceInfo] = field(default_factory=list)
    total_download_speed: Optional[float] = None
    total_upload_speed: Optional[float] = None
    total_bytes_recv: int = 0
    total_bytes_sent: int = 0
