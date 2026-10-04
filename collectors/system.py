"""Static system information (collected once, cached)."""
from __future__ import annotations

import getpass
import platform
import socket
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import psutil

from collectors.base import BaseCollector
from models.system import SystemInfo
from utils.platform_utils import IS_LINUX, IS_WINDOWS, read_registry_value

_BIOS_KEY = r"HARDWARE\DESCRIPTION\System\BIOS"
_NT_KEY = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"


def _dmi(name: str) -> Optional[str]:
    try:
        text = (Path("/sys/class/dmi/id") / name).read_text().strip()
        return text or None
    except OSError:
        return None


def _reg(key: str, name: str) -> Optional[str]:
    value = read_registry_value("HKEY_LOCAL_MACHINE", key, name)
    return str(value).strip() if value not in (None, "") else None


class SystemCollector(BaseCollector[SystemInfo]):
    name = "system"

    def __init__(self) -> None:
        self._info: Optional[SystemInfo] = None

    def collect(self) -> SystemInfo:
        if self._info is None:
            self._info = self._build()
        return self._info

    def _build(self) -> SystemInfo:
        try:
            boot = datetime.fromtimestamp(psutil.boot_time())
        except Exception:
            boot = None
        manufacturer = model = bios = os_build = None
        os_name, os_version = platform.system(), platform.release()
        if IS_WINDOWS:
            build_no = sys.getwindowsversion().build
            os_name = "Windows 11" if build_no >= 22000 else "Windows 10"
            ubr = read_registry_value("HKEY_LOCAL_MACHINE", _NT_KEY, "UBR")
            os_build = f"{build_no}.{ubr}" if ubr is not None else str(build_no)
            display = _reg(_NT_KEY, "DisplayVersion") or _reg(_NT_KEY, "ReleaseId")
            os_version = display or platform.version()
            manufacturer = _reg(_BIOS_KEY, "SystemManufacturer")
            model = _reg(_BIOS_KEY, "SystemProductName")
            parts = [_reg(_BIOS_KEY, "BIOSVendor"), _reg(_BIOS_KEY, "BIOSVersion")]
            date = _reg(_BIOS_KEY, "BIOSReleaseDate")
            bios = " ".join(p for p in parts if p) or None
            if bios and date:
                bios += f" ({date})"
        elif IS_LINUX:
            manufacturer, model = _dmi("sys_vendor"), _dmi("product_name")
            bios = " ".join(p for p in (_dmi("bios_vendor"), _dmi("bios_version")) if p) or None
            os_build = platform.release()
            os_version = platform.version()
        return SystemInfo(
            os_name=os_name, os_version=os_version, os_build=os_build,
            hostname=socket.gethostname(), manufacturer=manufacturer, model=model, bios=bios,
            architecture=platform.machine(), python_version=platform.python_version(), boot_time=boot,
        )
