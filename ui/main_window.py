"""Main window: sidebar + replaceable page area + status bar. Drains the monitoring queue."""
from __future__ import annotations

import logging
import tkinter as tk
from datetime import datetime
from typing import Callable, Optional

from config.constants import APP_NAME, INTERVAL_CHOICES_MS, PAGES
from config.settings import Settings, SettingsStore
from core.monitoring_service import MonitoringService
from models.snapshot import SystemSnapshot
from services.hardware_service import HardwareService
from ui.pages.base import BasePage, PageContext
from ui.pages.cpu_page import CPUPage
from ui.pages.dashboard_page import DashboardPage
from ui.pages.disk_page import DiskPage
from ui.pages.gpu_page import GPUPage
from ui.pages.memory_page import MemoryPage
from ui.pages.network_page import NetworkPage
from ui.pages.processes_page import ProcessesPage
from ui.pages.settings_page import SettingsPage
from ui.pages.system_page import SystemPage
from ui.styles.theme import configure_styles, get_palette
from ui.widgets.common import font
from ui.widgets.sidebar import Sidebar

log = logging.getLogger(__name__)
_PAGE_CLASSES: dict[str, type[BasePage]] = {
    "Dashboard": DashboardPage, "CPU": CPUPage, "Memory": MemoryPage, "GPU": GPUPage, "Disk": DiskPage,
    "Network": NetworkPage, "Processes": ProcessesPage, "System": SystemPage, "Settings": SettingsPage,
}
POLL_MS = 50   # how often the UI thread checks the queue (non-blocking, very cheap)


class MainWindow:
    def __init__(self, root: tk.Tk, store: SettingsStore, hardware: HardwareService,
                 service: MonitoringService, on_close: Callable[[], None]) -> None:
        self.root, self.store, self.hardware, self.service = root, store, hardware, service
        self._pages: dict[str, BasePage] = {}
        self._current: Optional[str] = None
        self._shell: Optional[tk.Frame] = None
        root.title(APP_NAME)
        root.geometry("1180x760")
        root.minsize(980, 640)
        root.protocol("WM_DELETE_WINDOW", on_close)
        store.subscribe(self._on_settings)
        self._build("Dashboard")

    # ---- construction ----------------------------------------------------------------
    def _build(self, start_page: str) -> None:
        palette = get_palette(self.store.settings.theme)
        configure_styles(self.root, palette)
        self.ctx = PageContext(palette, self.store, self.hardware.history, self.service)
        self._shell = tk.Frame(self.root, bg=palette.bg)
        self._shell.pack(fill="both", expand=True)
        self.sidebar = Sidebar(self._shell, palette, PAGES, self.show_page)
        self.sidebar.pack(side="left", fill="y")
        right = tk.Frame(self._shell, bg=palette.bg)
        right.pack(side="left", fill="both", expand=True)
        self.status = tk.Label(right, text="Waiting for first reading...", anchor="w", font=font(9),
                               fg=palette.muted, bg=palette.surface, padx=14, pady=5)
        self.status.pack(side="bottom", fill="x")
        self.content = tk.Frame(right, bg=palette.bg)
        self.content.pack(fill="both", expand=True)
        self._current = None
        self.show_page(start_page)

    def rebuild(self) -> None:
        """Re-create the whole UI (used for theme changes). Monitoring keeps running."""
        keep = self._current or "Dashboard"
        if self._current and self._current in self._pages:
            self._pages[self._current].on_hide()
        if self._shell is not None:
            self._shell.destroy()
        self._pages.clear()
        self._build(keep)

    # ---- navigation ------------------------------------------------------------------
    def show_page(self, name: str) -> None:
        if name == self._current:
            return
        if self._current and self._current in self._pages:
            self._pages[self._current].on_hide()
            self._pages[self._current].pack_forget()
        page = self._pages.get(name)
        if page is None:                      # lazy: pages are built on first visit
            page = self._pages[name] = _PAGE_CLASSES[name](self.content, self.ctx)
        page.pack(fill="both", expand=True)
        self._current = name
        self.sidebar.select(name)
        page.on_show()
        if self.hardware.latest is not None:
            self._safe_update(page, self.hardware.latest)

    # ---- data flow -------------------------------------------------------------------
    def start(self) -> None:
        self.root.after(POLL_MS, self._tick)

    def _tick(self) -> None:
        snap = self.service.poll()
        if snap is not None:
            self.hardware.update(snap)
            if self._current:
                self._safe_update(self._pages[self._current], snap)
            interval = next((k for k, v in INTERVAL_CHOICES_MS.items() if v == self.store.settings.interval_ms),
                            f"{self.store.settings.interval_ms} ms")
            self.status.configure(text=f"Updated {datetime.now():%H:%M:%S}  ·  interval {interval}  ·  "
                                       f"history {self.store.settings.history_seconds}s")
        self.root.after(POLL_MS, self._tick)

    @staticmethod
    def _safe_update(page: BasePage, snap: SystemSnapshot) -> None:
        try:
            page.update_view(snap)
        except Exception:                      # a UI bug must not stop monitoring
            log.exception("Page '%s' failed to update", page.title)

    def _on_settings(self, settings: Settings, changed: set[str]) -> None:
        if "theme" in changed:
            self.root.after_idle(self.rebuild)
