"""MonitoringService: one long-running worker thread -> bounded queue -> Tkinter.

The worker never touches Tk. The UI calls ``poll()`` from ``root.after`` and receives
only the newest snapshot (stale ones are dropped), so the UI can never fall behind.
"""
from __future__ import annotations

import logging
import queue
import threading
import time
from typing import Optional

from config.constants import QUEUE_MAXSIZE
from core.monitor_manager import MonitorManager
from models.snapshot import SystemSnapshot

log = logging.getLogger(__name__)


class MonitoringService:
    def __init__(self, manager: MonitorManager, interval_ms: int = 1000) -> None:
        self._manager = manager
        self._interval_s = interval_ms / 1000.0
        self._queue: "queue.Queue[SystemSnapshot]" = queue.Queue(maxsize=QUEUE_MAXSIZE)
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._force_processes = threading.Event()
        self._thread: Optional[threading.Thread] = None

    # ---- lifecycle -------------------------------------------------------------------
    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="monitor-worker", daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 3.0) -> None:
        self._stop.set()
        self._wake.set()
        if self._thread:
            self._thread.join(timeout)

    # ---- controls (safe to call from the UI thread) ----------------------------------
    def set_interval(self, interval_ms: int) -> None:
        self._interval_s = max(0.05, interval_ms / 1000.0)
        self._wake.set()                      # apply immediately

    def set_processes_enabled(self, enabled: bool) -> None:
        self._manager.processes_enabled = enabled
        if enabled:
            self.request_refresh(processes=True)

    def request_refresh(self, processes: bool = False) -> None:
        if processes:
            self._force_processes.set()
        self._wake.set()

    def poll(self) -> Optional[SystemSnapshot]:
        """Non-blocking: return the newest queued snapshot or None."""
        latest = None
        try:
            while True:
                latest = self._queue.get_nowait()
        except queue.Empty:
            pass
        return latest

    # ---- worker ----------------------------------------------------------------------
    def _publish(self, snapshot: SystemSnapshot) -> None:
        while True:
            try:
                self._queue.put_nowait(snapshot)
                return
            except queue.Full:
                try:
                    self._queue.get_nowait()   # drop the oldest
                except queue.Empty:
                    pass

    def _run(self) -> None:
        log.info("Monitoring worker started")
        try:
            while not self._stop.is_set():
                started = time.monotonic()
                try:
                    force = self._force_processes.is_set()
                    self._force_processes.clear()
                    self._publish(self._manager.collect_all(force_processes=force))
                except Exception:
                    log.exception("Monitoring cycle failed")
                remaining = self._interval_s - (time.monotonic() - started)
                if remaining > 0:
                    self._wake.wait(remaining)
                self._wake.clear()
        finally:
            self._manager.shutdown()          # COM / NVML cleanup on the owning thread
            log.info("Monitoring worker stopped")
