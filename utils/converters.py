"""Unit conversions."""
from __future__ import annotations

from typing import Optional


def celsius_to_fahrenheit(c: Optional[float]) -> Optional[float]:
    return None if c is None else c * 9 / 5 + 32


def mhz_to_ghz(mhz: Optional[float]) -> Optional[float]:
    return None if mhz is None else mhz / 1000


def bytes_to_mb(value: float) -> float:
    return value / (1024 * 1024)


def milliwatts_to_watts(mw: Optional[float]) -> Optional[float]:
    return None if mw is None else mw / 1000
