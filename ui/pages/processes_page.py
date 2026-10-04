from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from config.constants import MAX_PROCESS_ROWS
from models.snapshot import SystemSnapshot
from services.process_service import filter_and_sort
from ui.pages.base import BasePage
from ui.widgets.common import font, set_text
from ui.widgets.table import Column, TableView
from utils.formatters import NA, format_bytes

_SORT_LABELS = {"CPU": "cpu", "Memory": "memory", "Name": "name", "PID": "pid", "Threads": "threads"}
_HEADING_TO_SORT = {"cpu": "cpu", "mem": "memory", "name": "name", "pid": "pid", "thr": "threads",
                    "status": "status", "user": "user", "memp": "memory"}


class ProcessesPage(BasePage):
    title = "Processes"

    def build(self) -> None:
        body = tk.Frame(self, bg=self.p.bg)
        body.pack(fill="both", expand=True, padx=20, pady=16)
        self.header(body, "Processes", "Collected only while this page is open to keep the monitor lightweight")
        bar = tk.Frame(body, bg=self.p.bg)
        bar.pack(fill="x", pady=(0, 8))
        tk.Label(bar, text="Search", font=font(9), fg=self.p.muted, bg=self.p.bg).pack(side="left")
        self.query = tk.StringVar()
        entry = ttk.Entry(bar, textvariable=self.query, width=28)
        entry.pack(side="left", padx=(6, 16))
        self.query.trace_add("write", lambda *_: self._render())
        tk.Label(bar, text="Sort by", font=font(9), fg=self.p.muted, bg=self.p.bg).pack(side="left")
        self.sort_var = tk.StringVar(value="CPU")
        combo = ttk.Combobox(bar, textvariable=self.sort_var, values=list(_SORT_LABELS), state="readonly", width=10)
        combo.pack(side="left", padx=(6, 12))
        combo.bind("<<ComboboxSelected>>", lambda _e: self._on_combo())
        ttk.Button(bar, text="Refresh", style="Accent.TButton", command=self._refresh).pack(side="left")
        self.count = tk.Label(bar, text="", font=font(9), fg=self.p.muted, bg=self.p.bg)
        self.count.pack(side="right")
        self.table = TableView(body, self.p, [
            Column("pid", "PID", 60, "e"), Column("name", "Name", 200), Column("cpu", "CPU %", 65, "e"),
            Column("memp", "Mem %", 65, "e"), Column("mem", "Memory", 90, "e"), Column("thr", "Threads", 65, "e"),
            Column("status", "Status", 80), Column("user", "User", 150), Column("exe", "Executable", 380, stretch=True)],
            height=20, on_heading=self._on_heading)
        self.table.pack(fill="both", expand=True)
        self._sort_key, self._descending = "cpu", None
        self._snap: SystemSnapshot | None = None

    def on_show(self) -> None:
        self.ctx.service.set_processes_enabled(True)

    def on_hide(self) -> None:
        self.ctx.service.set_processes_enabled(False)

    def _on_combo(self) -> None:
        self._sort_key, self._descending = _SORT_LABELS[self.sort_var.get()], None
        self._render()

    def _on_heading(self, column: str) -> None:
        key = _HEADING_TO_SORT.get(column, "cpu")
        self._descending = (not self._descending) if key == self._sort_key and self._descending is not None else None
        if key == self._sort_key and self._descending is None:
            self._descending = False
        self._sort_key = key
        self._render()

    def _refresh(self) -> None:
        self.ctx.service.request_refresh(processes=True)

    def update_view(self, snap: SystemSnapshot) -> None:
        self._snap = snap
        self._render()

    def _render(self) -> None:
        info = self._snap.processes if self._snap else None
        if info is None:
            set_text(self.count, "Collecting process data...")
            return
        rows = filter_and_sort(info.processes, self.query.get(), self._sort_key, self._descending,
                               limit=MAX_PROCESS_ROWS)
        self.table.set_rows([(str(p.pid), (
            p.pid, p.name, f"{p.cpu_percent:.1f}", f"{p.memory_percent:.1f}", format_bytes(p.memory_bytes),
            p.threads, p.status, p.username or NA, p.executable or NA)) for p in rows])
        set_text(self.count, f"{len(info.processes)} processes · {info.total_threads:,} threads · "
                             f"showing {len(rows)}")
