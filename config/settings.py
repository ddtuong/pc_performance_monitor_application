"""User settings: typed dataclass + JSON persistence + change notification."""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any, Callable

from config import constants
from utils.logger import get_logger

log = get_logger(__name__)


def default_settings_path() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home())
    return Path(base) / "PCPerformanceMonitor" / "settings.json"


@dataclass
class Settings:
    interval_ms: int = 1000
    history_seconds: int = 60
    theme: str = "dark"                      # "dark" | "light"
    start_with_windows: bool = False
    start_minimized: bool = False
    enable_logging: bool = True
    log_level: str = "INFO"
    temperature_unit: str = "C"              # "C" | "F"
    usage_thresholds: tuple[float, float, float] = constants.DEFAULT_USAGE_THRESHOLDS
    temp_thresholds_c: tuple[float, float, float] = constants.DEFAULT_TEMP_THRESHOLDS_C
    visible_metrics: dict[str, bool] = field(default_factory=lambda: {
        "cpu": True, "ram": True, "gpu": True, "disk": True, "network": True, "temperature": True,
    })

    @property
    def history_points(self) -> int:
        points = int(self.history_seconds * 1000 / max(self.interval_ms, 1))
        return max(10, min(points, constants.MAX_HISTORY_POINTS))


class SettingsStore:
    """Loads/saves :class:`Settings` and notifies subscribers on change."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_settings_path()
        self.settings = Settings()
        self._listeners: list[Callable[[Settings, set[str]], None]] = []

    def load(self) -> Settings:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            log.info("Using default settings (%s)", exc)
            return self.settings
        known = {f.name for f in fields(Settings)}
        for key, value in raw.items():
            if key not in known:
                continue
            if key in ("usage_thresholds", "temp_thresholds_c") and isinstance(value, list) and len(value) == 3:
                value = tuple(float(v) for v in value)
            if key == "visible_metrics" and isinstance(value, dict):
                value = {**self.settings.visible_metrics, **value}
            setattr(self.settings, key, value)
        return self.settings

    def save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(asdict(self.settings), indent=2), encoding="utf-8")
        except OSError as exc:
            log.error("Could not save settings: %s", exc)

    def subscribe(self, listener: Callable[[Settings, set[str]], None]) -> None:
        self._listeners.append(listener)

    def update(self, **changes: Any) -> None:
        """Apply changes, persist, and notify listeners with the set of changed keys."""
        changed = {k for k, v in changes.items() if getattr(self.settings, k) != v}
        for key, value in changes.items():
            setattr(self.settings, key, value)
        if not changed:
            return
        self.save()
        for listener in list(self._listeners):
            try:
                listener(self.settings, changed)
            except Exception:  # a bad listener must not break settings
                log.exception("Settings listener failed")
