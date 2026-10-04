"""Performance-state classification (Normal / Moderate / High / Critical)."""
from __future__ import annotations

from enum import Enum
from typing import Optional, Sequence


class Level(str, Enum):
    NORMAL = "Normal"
    MODERATE = "Moderate"
    HIGH = "High"
    CRITICAL = "Critical"
    UNKNOWN = "N/A"


def classify(value: Optional[float], thresholds: Sequence[float]) -> Level:
    """``thresholds`` = (moderate, high, critical) lower bounds, ascending."""
    if value is None:
        return Level.UNKNOWN
    moderate, high, critical = thresholds
    if value >= critical:
        return Level.CRITICAL
    if value >= high:
        return Level.HIGH
    if value >= moderate:
        return Level.MODERATE
    return Level.NORMAL
