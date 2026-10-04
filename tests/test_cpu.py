import struct
from collections import namedtuple
from unittest.mock import MagicMock, patch

from collectors import cpu as cpu_module
from collectors.cpu import CPUCollector, parse_vendor
from collectors.cpu_topology import parse_core_records, validate_topology
from models.cpu import PhysicalCoreInfo
from models.sensor import SensorKind, SensorReading, SensorsInfo

Freq = namedtuple("Freq", "current min max")


def _make(logical=4, physical=2, freq=None, percpu_freq=None, sensors=None):
    fake = MagicMock()
    fake.cpu_count.side_effect = lambda logical=True: logical_count if logical else physical
    logical_count = logical
    fake.cpu_percent.side_effect = lambda percpu=False, **k: [10.0 * (i + 1) for i in range(logical)] if percpu else 25.0
    fake.cpu_freq.side_effect = lambda percpu=False: (percpu_freq if percpu else freq)
    fake.getloadavg.side_effect = AttributeError
    with patch.object(cpu_module, "psutil", fake), \
         patch.object(cpu_module, "get_cpu_name", return_value="Test CPU"), \
         patch.object(cpu_module, "get_cpu_vendor", return_value="Intel"), \
         patch.object(cpu_module, "get_base_frequency_mhz", return_value=2600.0), \
         patch.object(cpu_module, "read_topology", return_value=None):
        collector = CPUCollector(sensors)
        info = collector.collect()
    return info


def test_physical_and_logical_are_separate():
    info = _make(logical=12, physical=6)
    assert info.physical_cores == 6 and info.logical_processors == 12
    assert info.threads_per_core == 2
    assert len(info.logical_processors_info) == 12          # one entry per logical processor


def test_per_processor_usage_is_dynamic():
    for n in (4, 8, 16, 32):
        assert len(_make(logical=n, physical=n // 2).logical_processors_info) == n


def test_windows_style_single_frequency_does_not_fabricate_per_core_values():
    info = _make(logical=4, freq=Freq(3800, 0, 5000), percpu_freq=[Freq(3800, 0, 5000)])
    assert info.current_frequency_mhz == 3800 and info.max_frequency_mhz == 5000
    assert all(lp.frequency_mhz is None for lp in info.logical_processors_info)


def test_per_core_frequency_used_when_available():
    freqs = [Freq(3000 + i, 0, 5000) for i in range(4)]
    info = _make(logical=4, freq=Freq(3000, 0, 5000), percpu_freq=freqs)
    assert [lp.frequency_mhz for lp in info.logical_processors_info] == [3000, 3001, 3002, 3003]


def test_missing_sensors_give_none_not_fake_values():
    info = _make()
    assert info.temperature_celsius is None and info.power_watts is None


def test_sensor_values_are_used_when_present():
    sensors = MagicMock()
    sensors.latest = SensorsInfo([
        SensorReading("CPU Package", SensorKind.TEMPERATURE, 61.0, "°C", "Cpu"),
        SensorReading("CPU Package", SensorKind.POWER, 42.5, "W", "Cpu"),
        SensorReading("GPU Core", SensorKind.TEMPERATURE, 70.0, "°C", "GpuNvidia"),
    ])
    info = _make(sensors=sensors)
    assert info.package_temperature_celsius == 61.0 and info.power_watts == 42.5


def test_parse_vendor():
    assert parse_vendor("GenuineIntel") == "Intel"
    assert parse_vendor("AuthenticAMD") == "AMD"
    assert parse_vendor(None, "AMD Ryzen 7") == "AMD"


def _record(mask, eff=0, group=0):
    return struct.pack("<IIBB20sH", 0, 48, 0, eff, b"\0" * 20, 1) + struct.pack("<QH6x", mask, group)


def test_parse_windows_core_records_and_validate():
    buf = _record(0b0011) + _record(0b1100)
    cores = parse_core_records(buf)
    assert [c.logical_indices for c in cores] == [(0, 1), (2, 3)]
    assert validate_topology(cores, 4)
    assert not validate_topology(cores, 6)                  # incomplete mapping is rejected


def test_multi_group_topology_is_rejected_not_guessed():
    assert parse_core_records(_record(0b11, group=1)) == []


def test_validate_rejects_duplicates():
    cores = [PhysicalCoreInfo(0, (0, 1)), PhysicalCoreInfo(1, (1, 2))]
    assert not validate_topology(cores, 3)
