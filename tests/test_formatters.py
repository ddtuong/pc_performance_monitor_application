from utils.formatters import (format_bytes, format_duration, format_frequency, format_percentage,
                              format_speed, format_temperature)
from utils.levels import Level, classify


def test_format_bytes_units():
    assert format_bytes(512) == "512 B"
    assert format_bytes(1024) == "1 KB"
    assert format_bytes(1048576) == "1 MB"
    assert format_bytes(1073741824) == "1 GB"
    assert format_bytes(1610612736) == "1.5 GB"
    assert format_bytes(None) == "N/A"


def test_format_speed():
    assert format_speed(1048576) == "1 MB/s"
    assert format_speed(None) == "N/A"


def test_format_frequency():
    assert format_frequency(3800) == "3.80 GHz"
    assert format_frequency(800) == "800 MHz"
    assert format_frequency(None) == "N/A"
    assert format_frequency(0) == "N/A"


def test_format_duration():
    assert format_duration(45) == "45s"
    assert format_duration(3 * 3600 + 24 * 60) == "3h 24m"
    assert format_duration(90000) == "1d 1h 0m"
    assert format_duration(None) == "N/A"


def test_format_temperature_and_percentage():
    assert format_temperature(58) == "58 °C"
    assert format_temperature(100, "F") == "212 °F"
    assert format_temperature(None) == "N/A"
    assert format_percentage(42.4) == "42%"


def test_classify_levels():
    t = (50, 80, 95)
    assert classify(10, t) == Level.NORMAL
    assert classify(50, t) == Level.MODERATE
    assert classify(80, t) == Level.HIGH
    assert classify(99, t) == Level.CRITICAL
    assert classify(None, t) == Level.UNKNOWN
