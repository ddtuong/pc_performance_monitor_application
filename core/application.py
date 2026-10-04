"""Application wiring: settings -> logging -> monitoring -> UI."""
from __future__ import annotations

import logging
import sys
import tkinter as tk
from pathlib import Path

from config.settings import Settings, SettingsStore
from core.monitor_manager import MonitorManager
from core.monitoring_service import MonitoringService
from services.hardware_service import HardwareService
from ui.main_window import MainWindow
from utils.logger import setup_logging
from utils.platform_utils import set_startup_enabled

log = logging.getLogger(__name__)


def _startup_command() -> str:
    exe = Path(sys.executable)
    pythonw = exe.with_name("pythonw.exe")           # no console window at login
    launcher = pythonw if pythonw.exists() else exe
    script = Path(__file__).resolve().parent.parent / "app.py"
    return f'"{launcher}" "{script}"'


class Application:
    def __init__(self) -> None:
        self.store = SettingsStore()
        settings = self.store.load()
        setup_logging(settings.enable_logging, settings.log_level)
        log.info("Starting application")
        self.manager = MonitorManager.create_default()
        self.service = MonitoringService(self.manager, settings.interval_ms)
        self.hardware = HardwareService(settings.history_points)
        self.root = tk.Tk()
        self.window = MainWindow(self.root, self.store, self.hardware, self.service, self.shutdown)
        self.store.subscribe(self._on_settings)
        if settings.start_minimized:
            self.root.iconify()

    def _on_settings(self, settings: Settings, changed: set[str]) -> None:
        if {"interval_ms", "history_seconds"} & changed:
            self.hardware.set_history_points(settings.history_points)
        if "interval_ms" in changed:
            self.service.set_interval(settings.interval_ms)
            self.hardware.set_history_points(settings.history_points)
        if {"enable_logging", "log_level"} & changed:
            setup_logging(settings.enable_logging, settings.log_level)
        if "start_with_windows" in changed and not set_startup_enabled(settings.start_with_windows, _startup_command()):
            log.warning("Start-with-Windows could not be applied (not Windows, or registry access denied)")

    def run(self) -> None:
        self.service.start()
        self.window.start()
        self.root.mainloop()

    def shutdown(self) -> None:
        log.info("Shutting down")
        self.service.stop()
        self.root.destroy()
