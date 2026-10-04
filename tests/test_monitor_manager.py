import time

from collectors.base import BaseCollector
from core.exceptions import PermissionDenied
from core.monitor_manager import MonitorManager
from core.monitoring_service import MonitoringService
from models.snapshot import MetricState
from services.hardware_service import HardwareService, HistoryStore


class Fixed(BaseCollector):
    def __init__(self, value):
        self.value, self.calls, self.closed = value, 0, False

    def collect(self):
        self.calls += 1
        return self.value

    def shutdown(self):
        self.closed = True


class Failing(BaseCollector):
    def __init__(self, exc):
        self.exc = exc

    def collect(self):
        raise self.exc


def test_failing_collectors_do_not_break_the_snapshot():
    manager = MonitorManager({"memory": Fixed("MEM"), "sensors": Failing(PermissionDenied("no admin")),
                              "gpu": Failing(RuntimeError("driver exploded"))})
    snap = manager.collect_all()
    assert snap.memory == "MEM"
    assert snap.sensors is None and snap.gpu is None
    assert snap.statuses["memory"].state == MetricState.AVAILABLE
    assert snap.statuses["sensors"].state == MetricState.PERMISSION_DENIED
    assert snap.statuses["sensors"].message == "no admin"
    assert snap.statuses["gpu"].state == MetricState.UNAVAILABLE


def test_processes_only_collected_when_enabled_and_rate_limited():
    now = [0.0]
    procs = Fixed("PROCS")
    manager = MonitorManager({"processes": procs}, clock=lambda: now[0])
    manager.collect_all()
    assert procs.calls == 0                                   # disabled by default
    manager.processes_enabled = True
    manager.collect_all()
    assert procs.calls == 1
    now[0] = 0.5
    assert manager.collect_all().processes == "PROCS"         # served from cache, no new call
    assert procs.calls == 1
    now[0] = 0.6
    manager.collect_all(force_processes=True)                 # manual refresh bypasses the limit
    assert procs.calls == 2


def test_service_delivers_latest_snapshot_and_cleans_up():
    collector = Fixed("MEM")
    manager = MonitorManager({"memory": collector})
    service = MonitoringService(manager, interval_ms=50)
    service.start()
    time.sleep(0.4)
    snap = service.poll()
    service.stop()
    assert snap is not None and snap.memory == "MEM"
    assert collector.closed                                   # shutdown ran on the worker thread
    assert service._queue.qsize() <= 2                        # bounded queue


def test_history_is_bounded_and_resizable():
    store = HistoryStore(5)
    for i in range(20):
        store.append("x", float(i))
    assert store.get("x") == [15.0, 16.0, 17.0, 18.0, 19.0]
    store.resize(3)
    assert store.get("x") == [17.0, 18.0, 19.0]


def test_hardware_service_records_series():
    manager = MonitorManager({"memory": Fixed(None)})
    hw = HardwareService(10)
    hw.update(manager.collect_all())
    assert hw.history.get("cpu.usage") == [None]              # missing metric -> gap, never a fake 0
