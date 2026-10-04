from pathlib import Path
import tempfile

from config.settings import SettingsStore


def test_roundtrip_and_notification():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "s.json"
        store = SettingsStore(path)
        seen = []
        store.subscribe(lambda s, changed: seen.append(changed))
        store.update(interval_ms=500, theme="light")
        store.update(interval_ms=500)                       # no change -> no notification
        assert seen == [{"interval_ms", "theme"}]
        reloaded = SettingsStore(path).load()
        assert reloaded.interval_ms == 500 and reloaded.theme == "light"
        assert isinstance(reloaded.usage_thresholds, tuple)


def test_history_points_are_bounded():
    store = SettingsStore(Path("/nonexistent/x.json"))
    store.settings.interval_ms, store.settings.history_seconds = 100, 600
    assert store.settings.history_points == 600             # capped by MAX_HISTORY_POINTS
    store.settings.interval_ms, store.settings.history_seconds = 1000, 60
    assert store.settings.history_points == 60
