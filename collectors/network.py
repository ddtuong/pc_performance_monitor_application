"""Network collector: per-interface counters, addresses, and up/down speeds from deltas."""
from __future__ import annotations

import socket
import time
from typing import Optional

import psutil

from collectors.base import BaseCollector
from config.constants import ADDRESS_REFRESH_S
from models.network import NetworkInfo, NetworkInterfaceInfo
from utils.logger import get_logger
from utils.rates import RateTracker

log = get_logger(__name__)
_LOOPBACK_HINTS = ("loopback", "lo")


def is_loopback(name: str) -> bool:
    n = name.lower()
    return n == "lo" or "loopback" in n


class NetworkCollector(BaseCollector[NetworkInfo]):
    name = "network"

    def __init__(self, rates: Optional[RateTracker] = None) -> None:
        self._rates = rates or RateTracker()
        self._addr_cache: dict[str, tuple[list[str], list[str], str]] = {}
        self._stats_cache: dict = {}
        self._cache_time = 0.0

    def _refresh_static(self) -> None:
        """Addresses/link state change rarely: refresh every few seconds, not every tick."""
        if time.monotonic() - self._cache_time < ADDRESS_REFRESH_S and self._addr_cache:
            return
        cache: dict[str, tuple[list[str], list[str], str]] = {}
        for nic, addrs in psutil.net_if_addrs().items():
            v4 = [a.address for a in addrs if a.family == socket.AF_INET]
            v6 = [a.address.split("%")[0] for a in addrs if a.family == socket.AF_INET6]
            mac = next((a.address for a in addrs if a.family == psutil.AF_LINK), "")
            cache[nic] = (v4, v6, mac)
        self._addr_cache = cache
        self._stats_cache = psutil.net_if_stats()
        self._cache_time = time.monotonic()

    def collect(self) -> NetworkInfo:
        self._refresh_static()
        counters = psutil.net_io_counters(pernic=True)
        interfaces: list[NetworkInterfaceInfo] = []
        live = set()
        for nic, c in counters.items():
            v4, v6, mac = self._addr_cache.get(nic, ([], [], ""))
            stats = self._stats_cache.get(nic)
            keys = ((nic, "down"), (nic, "up"))
            live.update(keys)
            interfaces.append(NetworkInterfaceInfo(
                name=nic, is_up=bool(stats and stats.isup), speed_mbps=stats.speed if stats else 0,
                ipv4=v4, ipv6=v6, mac=mac,
                bytes_sent=c.bytes_sent, bytes_recv=c.bytes_recv,
                packets_sent=c.packets_sent, packets_recv=c.packets_recv,
                errors_in=c.errin, errors_out=c.errout, dropped_in=c.dropin, dropped_out=c.dropout,
                download_speed=self._rates.update(keys[0], c.bytes_recv),
                upload_speed=self._rates.update(keys[1], c.bytes_sent),
            ))
        self._rates.forget_missing(live)
        interfaces.sort(key=lambda i: (not i.is_up, i.name.lower()))
        real = [i for i in interfaces if not is_loopback(i.name)]   # avoid double counting
        downs = [i.download_speed for i in real if i.download_speed is not None]
        ups = [i.upload_speed for i in real if i.upload_speed is not None]
        return NetworkInfo(
            interfaces=interfaces,
            total_download_speed=sum(downs) if downs else None,
            total_upload_speed=sum(ups) if ups else None,
            total_bytes_recv=sum(i.bytes_recv for i in real),
            total_bytes_sent=sum(i.bytes_sent for i in real),
        )
