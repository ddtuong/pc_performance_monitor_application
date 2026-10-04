from utils.scale import nice_ceiling


def test_nice_ceiling():
    assert nice_ceiling(0) == 1.0
    assert nice_ceiling(0.7) == 1.0
    assert nice_ceiling(130) == 200
    assert nice_ceiling(4_300_000) == 5_000_000
