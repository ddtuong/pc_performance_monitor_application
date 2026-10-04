"""Collector contract. Collectors talk to the OS/hardware and return typed models.

Rules: collectors never import Tkinter, never fake values, and raise
:class:`core.exceptions.CollectorError` when a whole category is unavailable.
Individual missing metrics are returned as ``None``.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class BaseCollector(ABC, Generic[T]):
    name: str = "base"

    @abstractmethod
    def collect(self) -> T:
        """Return the current reading. Runs on the monitoring worker thread."""

    def shutdown(self) -> None:
        """Release resources. Called on the worker thread when monitoring stops."""
