from __future__ import annotations

import time
from datetime import datetime
from typing import Optional


def uptime_seconds(boot_time: Optional[datetime]) -> Optional[float]:
    if boot_time is None:
        return None
    return max(0.0, time.time() - boot_time.timestamp())


def format_datetime(value: Optional[datetime]) -> str:
    return "N/A" if value is None else value.strftime("%Y-%m-%d %H:%M:%S")
