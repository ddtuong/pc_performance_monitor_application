"""Pure text-formatting helpers. No UI or hardware imports live here."""
from __future__ import annotations

from typing import Optional

NA = "N/A"
_BYTE_UNITS = ("B", "KB", "MB", "GB", "TB", "PB")


def format_bytes(value: Optional[float], decimals: int = 1) -> str:
    """1024 -> '1 KB', 1048576 -> '1 MB', 1073741824 -> '1 GB'."""
    if value is None:
        return NA
    size = float(value)
    sign = "-" if size < 0 else ""
    size = abs(size)
    unit = 0
    while size >= 1024 and unit < len(_BYTE_UNITS) - 1:
        size /= 1024
        unit += 1
    if unit == 0:
        return f"{sign}{int(size)} B"
    text = f"{size:.{decimals}f}".rstrip("0").rstrip(".")
    return f"{sign}{text} {_BYTE_UNITS[unit]}"


def format_speed(bytes_per_second: Optional[float], decimals: int = 1) -> str:
    """Format a throughput value, e.g. 1048576 -> '1 MB/s'."""
    if bytes_per_second is None:
        return NA
    return f"{format_bytes(bytes_per_second, decimals)}/s"


def format_frequency(mhz: Optional[float]) -> str:
    """3800 -> '3.80 GHz', 800 -> '800 MHz'."""
    if mhz is None or mhz <= 0:
        return NA
    if mhz >= 1000:
        return f"{mhz / 1000:.2f} GHz"
    return f"{mhz:.0f} MHz"


def format_duration(seconds: Optional[float]) -> str:
    """12240 -> '3h 24m'. Includes days when >= 24h."""
    if seconds is None or seconds < 0:
        return NA
    total = int(seconds)
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    if days:
        return f"{days}d {hours}h {minutes}m"
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def format_temperature(celsius: Optional[float], unit: str = "C") -> str:
    """58 -> '58 °C' (or '136 °F' when unit == 'F')."""
    if celsius is None:
        return NA
    if unit.upper() == "F":
        return f"{celsius * 9 / 5 + 32:.0f} °F"
    return f"{celsius:.0f} °C"


def format_percentage(value: Optional[float], decimals: int = 0) -> str:
    if value is None:
        return NA
    return f"{value:.{decimals}f}%"


def format_power(watts: Optional[float]) -> str:
    return NA if watts is None else f"{watts:.1f} W"


def format_rpm(rpm: Optional[float]) -> str:
    return NA if rpm is None else f"{rpm:,.0f} RPM"


def format_count(value: Optional[float]) -> str:
    return NA if value is None else f"{value:,.0f}"
