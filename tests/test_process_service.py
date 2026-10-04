from models.process import ProcessInfo
from services.process_service import filter_and_sort


def _p(pid, name, cpu, mem, user="me"):
    return ProcessInfo(pid, name, cpu, 1.0, mem, 4, "running", user, f"C:\\{name}.exe")


PROCS = [_p(1, "alpha", 5.0, 300), _p(2, "Beta", 50.0, 100), _p(3, "gamma", 20.0, 900, "other")]


def test_sort_by_cpu_and_memory_descending_by_default():
    assert [p.pid for p in filter_and_sort(PROCS, sort_key="cpu")] == [2, 3, 1]
    assert [p.pid for p in filter_and_sort(PROCS, sort_key="memory")] == [3, 1, 2]


def test_sort_by_name_is_ascending_and_case_insensitive():
    assert [p.name for p in filter_and_sort(PROCS, sort_key="name")] == ["alpha", "Beta", "gamma"]


def test_search_by_name_pid_user_and_limit():
    assert [p.pid for p in filter_and_sort(PROCS, query="BET")] == [2]
    assert [p.pid for p in filter_and_sort(PROCS, query="3")] == [3]
    assert [p.pid for p in filter_and_sort(PROCS, query="other")] == [3]
    assert len(filter_and_sort(PROCS, limit=2)) == 2
