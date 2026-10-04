from collections import namedtuple
from unittest.mock import patch

from collectors import disk as disk_module
from collectors.disk import DiskCollector
from utils.rates import RateTracker

IO = namedtuple("IO", "read_count write_count read_bytes write_bytes")
Usage = namedtuple("Usage", "total used free percent")
Part = namedtuple("Part", "device mountpoint fstype opts")


def test_disk_speed_is_delta_over_elapsed_time():
    now = [0.0]
    collector = DiskCollector(RateTracker(clock=lambda: now[0]))
    samples = iter([{"PhysicalDrive0": IO(100, 50, 1_000, 500)},
                    {"PhysicalDrive0": IO(300, 150, 5_000, 2_500)}])
    with patch.object(disk_module.psutil, "disk_io_counters", side_effect=lambda perdisk: next(samples)):
        first = collector.collect_io()
        now[0] = 2.0
        second = collector.collect_io()
    assert first[0].read_speed is None                      # no previous sample yet
    assert second[0].read_speed == 2000.0                   # (5000-1000)/2s
    assert second[0].write_speed == 1000.0
    assert second[0].read_ops_per_s == 100.0                # (300-100)/2s


def test_io_unavailable_is_reported_not_crashed():
    collector = DiskCollector()
    with patch.object(disk_module.psutil, "disk_io_counters", side_effect=RuntimeError("boom")):
        assert collector.collect_io() is None


def test_partitions_skip_unreadable_and_cdrom():
    parts = [Part("C:", "C:\\", "NTFS", "rw"), Part("D:", "D:\\", "", "cdrom"), Part("E:", "E:\\", "FAT", "rw")]

    def usage(mount):
        if mount == "E:\\":
            raise PermissionError
        return Usage(1000, 400, 600, 40.0)

    with patch.object(disk_module.psutil, "disk_partitions", return_value=parts), \
         patch.object(disk_module.psutil, "disk_usage", side_effect=usage):
        result = DiskCollector().collect_partitions()
    assert [p.device for p in result] == ["C:"]
    assert result[0].percent == 40.0
