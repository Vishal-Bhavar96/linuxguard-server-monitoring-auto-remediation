"""
Unit tests for Process Monitor Engine.
"""

from monitoring.engines.process_monitor import ProcessMonitor


def test_get_all_processes():
    procs = ProcessMonitor.get_all_processes()
    assert isinstance(procs, list)
    assert len(procs) > 0
    first = procs[0]
    assert 'pid' in first
    assert 'name' in first
    assert 'cpu_percent' in first
    assert 'memory_percent' in first
    assert 'username' in first
    assert 'status' in first


def test_get_top_processes_sorting():
    top_cpu = ProcessMonitor.get_top_processes(limit=5, sort_by='cpu')
    assert len(top_cpu) <= 5
    if len(top_cpu) >= 2:
        assert top_cpu[0]['cpu_percent'] >= top_cpu[1]['cpu_percent']

    top_mem = ProcessMonitor.get_top_processes(limit=5, sort_by='memory')
    assert len(top_mem) <= 5
    if len(top_mem) >= 2:
        assert top_mem[0]['memory_percent'] >= top_mem[1]['memory_percent']


def test_process_filtering():
    # Filter by known substring or empty
    procs = ProcessMonitor.get_top_processes(limit=10, filter_name='python')
    assert isinstance(procs, list)
