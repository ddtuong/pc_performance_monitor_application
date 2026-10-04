"""Pure filtering/sorting for the process table."""
from __future__ import annotations

from typing import Iterable

from models.process import ProcessInfo

SORT_KEYS = {
    "cpu": lambda p: p.cpu_percent,
    "memory": lambda p: p.memory_bytes,
    "name": lambda p: p.name.lower(),
    "pid": lambda p: p.pid,
    "threads": lambda p: p.threads,
    "status": lambda p: p.status,
    "user": lambda p: (p.username or "").lower(),
}
_TEXT_KEYS = {"name", "status", "user"}


def filter_and_sort(processes: Iterable[ProcessInfo], query: str = "", sort_key: str = "cpu",
                    descending: bool | None = None, limit: int | None = None) -> list[ProcessInfo]:
    """Filter by name/PID/user/exe substring, then sort. Numeric keys default to descending."""
    q = query.strip().lower()
    items = [p for p in processes if not q or q in p.name.lower() or q == str(p.pid)
             or q in (p.username or "").lower() or q in (p.executable or "").lower()]
    if descending is None:
        descending = sort_key not in _TEXT_KEYS and sort_key != "pid"
    items.sort(key=SORT_KEYS.get(sort_key, SORT_KEYS["cpu"]), reverse=descending)
    return items[:limit] if limit else items
