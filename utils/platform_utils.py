"""Platform helpers (Windows-first, safe no-ops elsewhere)."""
from __future__ import annotations

import sys
from typing import Optional

from utils.logger import get_logger

log = get_logger(__name__)
IS_WINDOWS = sys.platform == "win32"
IS_LINUX = sys.platform.startswith("linux")

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_APP_VALUE = "PCPerformanceMonitor"


def read_registry_value(hive: str, path: str, name: str) -> Optional[object]:
    """Read one registry value on Windows; None on any failure or other OS."""
    if not IS_WINDOWS:
        return None
    try:
        import winreg

        root = getattr(winreg, hive)
        with winreg.OpenKey(root, path) as key:
            return winreg.QueryValueEx(key, name)[0]
    except (OSError, ImportError) as exc:
        log.debug("Registry read failed %s\\%s\\%s: %s", hive, path, name, exc)
        return None


def set_startup_enabled(enabled: bool, command: str) -> bool:
    """Add/remove the app from the current user's Windows startup. Returns success."""
    if not IS_WINDOWS:
        return False
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            if enabled:
                winreg.SetValueEx(key, _APP_VALUE, 0, winreg.REG_SZ, command)
            else:
                try:
                    winreg.DeleteValue(key, _APP_VALUE)
                except FileNotFoundError:
                    pass
        return True
    except OSError as exc:
        log.error("Could not update startup entry: %s", exc)
        return False
