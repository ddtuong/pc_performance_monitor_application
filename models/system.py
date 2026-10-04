from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class SystemInfo:
    os_name: str
    os_version: str
    os_build: Optional[str]
    hostname: str
    manufacturer: Optional[str]
    model: Optional[str]
    bios: Optional[str]
    architecture: str
    python_version: str
    boot_time: Optional[datetime]
