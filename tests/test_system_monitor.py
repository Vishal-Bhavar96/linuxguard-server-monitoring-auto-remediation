"""
Unit tests for System Monitor Engine (psutil telemetry collection).
"""

from monitoring.engines.system_monitor import (
    get_cpu_usage, get_memory_usage, get_disk_usage,
    get_load_average, get_network_usage, get_uptime, SystemMonitor
)


def test_get_cpu_usage():
    cpu = get_cpu_usage()
    assert 'cpu_percent' in cpu
    assert isinstance(cpu['cpu_percent'], float)
    assert 0.0 <= cpu['cpu_percent'] <= 100.0
    assert 'logical_cores' in cpu
    assert cpu['logical_cores'] >= 1
    assert isinstance(cpu['per_cpu'], list)


def test_get_memory_usage():
    mem = get_memory_usage()
    assert 'memory_percent' in mem
    assert 0.0 <= mem['memory_percent'] <= 100.0
    assert 'total_mb' in mem
    assert mem['total_mb'] > 0
    assert 'used_mb' in mem
    assert 'free_mb' in mem


def test_get_disk_usage():
    disk = get_disk_usage()
    assert 'disk_percent' in disk
    assert 0.0 <= disk['disk_percent'] <= 100.0
    assert 'total_gb' in disk
    assert disk['total_gb'] > 0
    assert 'partitions' in disk
    assert isinstance(disk['partitions'], list)


def test_get_load_average():
    load = get_load_average()
    assert 'load1' in load
    assert 'load5' in load
    assert 'load15' in load
    assert 'formatted' in load
    assert isinstance(load['load1'], float)


def test_get_network_usage():
    net = get_network_usage()
    assert 'bytes_sent' in net
    assert 'bytes_recv' in net
    assert net['bytes_sent'] >= 0
    assert net['bytes_recv'] >= 0


def test_get_uptime():
    uptime = get_uptime()
    assert 'uptime_seconds' in uptime
    assert uptime['uptime_seconds'] >= 0
    assert 'formatted' in uptime
    assert isinstance(uptime['formatted'], str)


def test_collect_snapshot():
    snapshot = SystemMonitor.collect_snapshot()
    assert 'cpu' in snapshot
    assert 'memory' in snapshot
    assert 'disk' in snapshot
    assert 'load_average' in snapshot
    assert 'network' in snapshot
    assert 'uptime' in snapshot
