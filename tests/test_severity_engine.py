"""
Unit tests for Severity Engine and Root Cause Analysis Engine.
"""

from monitoring.engines.severity_engine import SeverityEngine
from monitoring.engines.root_cause_engine import RootCauseEngine


def test_metric_severity_calculations():
    # Below warning
    assert SeverityEngine.evaluate_metric_severity('CPU', 50.0, 85.0, 95.0) == 'LOW'
    # Near warning
    assert SeverityEngine.evaluate_metric_severity('CPU', 86.0, 85.0, 95.0) == 'MEDIUM'
    # High zone
    assert SeverityEngine.evaluate_metric_severity('CPU', 92.0, 85.0, 95.0) == 'HIGH'
    # Critical zone
    assert SeverityEngine.evaluate_metric_severity('CPU', 97.0, 85.0, 95.0) == 'CRITICAL'


def test_service_severity_calculation():
    assert SeverityEngine.evaluate_service_severity('nginx', 'FAILED') == 'CRITICAL'
    assert SeverityEngine.evaluate_service_severity('nginx', 'INACTIVE') == 'HIGH'
    assert SeverityEngine.evaluate_service_severity('unknown_aux', 'FAILED') == 'HIGH'


def test_security_severity():
    assert SeverityEngine.evaluate_security_severity('SSH_BRUTE_FORCE', 5) == 'HIGH'
    assert SeverityEngine.evaluate_security_severity('SSH_BRUTE_FORCE', 25) == 'CRITICAL'


def test_root_cause_cpu_process_diagnosis():
    top_processes = [
        {'pid': 9999, 'name': 'node_worker', 'cpu_percent': 85.0, 'memory_percent': 12.0, 'username': 'ubuntu'}
    ]
    diag = RootCauseEngine.diagnose_cpu_incident(cpu_usage=92.0, top_processes=top_processes)
    assert 'Runaway High CPU Process' in diag['probable_cause']
    assert 'node_worker' in diag['probable_cause']
    assert 'PID 9999' in diag['probable_cause']
    assert diag['confidence'] >= 90.0
    assert 'recommendation' in diag
    assert 'evidence' in diag


def test_root_cause_disk_diagnosis():
    diag = RootCauseEngine.diagnose_disk_incident(disk_usage=94.0, mountpoint='/var/log')
    assert 'Filesystem Capacity Exhaustion' in diag['probable_cause']
    assert '/var/log' in diag['probable_cause']
    assert diag['confidence'] >= 80.0
