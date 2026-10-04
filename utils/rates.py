"""Delta-based rate calculation.

Cumulative OS counters (bytes read, bytes sent, ...) are NOT speeds. A speed is
``(current - previous) / elapsed_seconds``. :class:`RateTracker` keeps the previous
sample per key and handles first samples and counter resets safely.
"""
from __future__ import annotations

import time
from typing import Callable, Hashable, Optional


def compute_rate(previous: float, current: float, elapsed: float) -> float:
    """Return units/second. Counter resets (current < previous) and bad dt give 0."""
    if elapsed <= 0 or current < previous:
        return 0.0
    return (current - previous) / elapsed


class RateTracker:
    """Track many cumulative counters and turn them into per-second rates."""

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._last: dict[Hashable, tuple[float, float]] = {}

    def update(self, key: Hashable, value: float) -> Optional[float]:
        """Record ``value`` for ``key``; return the rate, or None on the first sample."""
        now = self._clock()
        previous = self._last.get(key)
        self._last[key] = (now, value)
        if previous is None:
            return None
        return compute_rate(previous[1], value, now - previous[0])

    def forget_missing(self, live_keys: set) -> None:
        for key in [k for k in self._last if k not in live_keys]:
            del self._last[key]
