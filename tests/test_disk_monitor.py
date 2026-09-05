"""
Unit tests for Disk and Network Monitor Engines.
"""

from monitoring.engines.disk_monitor import DiskMonitor
from monitoring.engines.network_monitor import NetworkMonitor


def test_disk_report_structure():
    report = DiskMonitor.get_disk_report(warn_threshold=80.0, crit_threshold=90.0)
    assert 'partitions' in report
    assert 'max_usage_percent' in report
    assert 'alerts' in report
    assert isinstance(report['partitions'], list)


def test_network_overview_structure():
    report = NetworkMonitor.get_network_overview()
    assert 'bytes_sent' in report
    assert 'bytes_recv' in report
    assert 'interfaces' in report
    assert 'connection_counts' in report
    assert isinstance(report['interfaces'], list)
    assert 'ESTABLISHED' in report['connection_counts']
    assert 'LISTEN' in report['connection_counts']
