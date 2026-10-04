"""Axis scaling helpers (pure math, no UI imports)."""
from __future__ import annotations

import math


def nice_ceiling(peak: float) -> float:
    """Round ``peak`` up to 1/2/5 x 10^n so auto-scaled axes have clean labels."""
    if peak <= 0:
        return 1.0
    base = 10 ** math.floor(math.log10(peak))
    for mult in (1, 2, 5, 10):
        if peak <= mult * base:
            return mult * base
    return 10 * base
