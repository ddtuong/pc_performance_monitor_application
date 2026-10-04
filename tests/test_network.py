import socket
from collections import namedtuple
from unittest.mock import patch

from collectors import network as net_module
from collectors.network import NetworkCollector, is_loopback
from utils.rates import RateTracker

IO = namedtuple("IO", "bytes_sent bytes_recv packets_sent packets_recv errin errout dropin dropout")
Addr = namedtuple("Addr", "family address netmask broadcast ptp")
Stats = namedtuple("Stats", "isup duplex speed mtu")


def _patches(counters):
    addrs = {"Ethernet": [Addr(socket.AF_INET, "192.168.1.5", None, None, None),
                          Addr(socket.AF_INET6, "fe80::1%eth0", None, None, None)]}
    stats = {"Ethernet": Stats(True, 2, 1000, 1500)}
    return (patch.object(net_module.psutil, "net_if_addrs", return_value=addrs),
            patch.object(net_module.psutil, "net_if_stats", return_value=stats),
            patch.object(net_module.psutil, "net_io_counters", side_effect=lambda pernic: next(counters)))


def test_download_upload_speed_from_two_measurements():
    now = [0.0]
    collector = NetworkCollector(RateTracker(clock=lambda: now[0]))
    counters = iter([{"Ethernet": IO(1000, 2000, 10, 20, 0, 0, 0, 0)},
                     {"Ethernet": IO(5000, 10000, 50, 90, 1, 2, 3, 4)}])
    p1, p2, p3 = _patches(counters)
    with p1, p2, p3:
        first = collector.collect()
        now[0] = 4.0
        second = collector.collect()
    assert first.total_download_speed is None
    nic = second.interfaces[0]
    assert nic.download_speed == 2000.0 and nic.upload_speed == 1000.0     # 8000/4s, 4000/4s
    assert nic.ipv4 == ["192.168.1.5"] and nic.ipv6 == ["fe80::1"]          # zone id stripped
    assert (nic.errors_in, nic.errors_out, nic.dropped_in, nic.dropped_out) == (1, 2, 3, 4)
    assert second.total_download_speed == 2000.0


def test_loopback_excluded_from_totals():
    assert is_loopback("lo") and is_loopback("Loopback Pseudo-Interface 1")
    assert not is_loopback("Ethernet")
