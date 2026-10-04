from utils.rates import RateTracker, compute_rate


def test_compute_rate_basic_and_reset():
    assert compute_rate(1000, 3000, 2.0) == 1000.0
    assert compute_rate(5000, 100, 1.0) == 0.0      # counter reset
    assert compute_rate(0, 100, 0) == 0.0           # bad dt


def test_tracker_first_sample_is_none_then_delta():
    times = iter([10.0, 12.0, 13.0])
    tracker = RateTracker(clock=lambda: next(times))
    assert tracker.update("k", 0) is None
    assert tracker.update("k", 2000) == 1000.0       # 2000 bytes in 2 s
    assert tracker.update("k", 2500) == 500.0


def test_forget_missing():
    tracker = RateTracker(clock=lambda: 1.0)
    tracker.update("a", 1)
    tracker.update("b", 1)
    tracker.forget_missing({"a"})
    assert tracker.update("b", 5) is None            # b was forgotten -> first sample again
