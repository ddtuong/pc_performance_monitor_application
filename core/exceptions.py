"""Exceptions that carry a user-facing availability state."""
from __future__ import annotations

from models.snapshot import MetricState


class CollectorError(Exception):
    """Base class for collector problems."""

    state = MetricState.UNAVAILABLE

    def __init__(self, message: str, state: MetricState | None = None) -> None:
        super().__init__(message)
        if state is not None:
            self.state = state


class HardwareNotDetected(CollectorError):
    state = MetricState.HARDWARE_NOT_DETECTED


class ApiUnavailable(CollectorError):
    state = MetricState.API_UNAVAILABLE


class NotSupported(CollectorError):
    state = MetricState.NOT_SUPPORTED


class PermissionDenied(CollectorError):
    state = MetricState.PERMISSION_DENIED
