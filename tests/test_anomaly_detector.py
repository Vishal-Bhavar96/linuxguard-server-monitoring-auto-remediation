"""
Unit tests for Anomaly Detection Engine and duplicate incident prevention.
"""

import pytest
from monitoring.models import Incident, Server
from monitoring.engines.anomaly_detector import AnomalyDetector


@pytest.mark.django_db
def test_cpu_anomaly_detection(test_server, default_threshold_settings):
    # High CPU Telemetry (96% -> Critical)
    telemetry = {
        'cpu': {'cpu_percent': 96.5},
        'memory': {'memory_percent': 45.0, 'swap_percent': 0.0},
        'disk': {'disk_percent': 50.0, 'mountpoint': '/'}
    }
    top_procs = [{'pid': 1234, 'name': 'stress_worker', 'cpu_percent': 88.0, 'memory_percent': 10.0, 'username': 'root'}]

    incidents = AnomalyDetector.process_system_telemetry(test_server, telemetry, top_procs)
    assert len(incidents) == 1
    inc = incidents[0]
    assert inc.category == Incident.Category.CPU
    assert inc.severity == Incident.Severity.CRITICAL
    assert 'High CPU' in inc.title
    assert inc.confidence >= 90.0

    # Test Duplicate Prevention on subsequent cycle
    incidents_second_cycle = AnomalyDetector.process_system_telemetry(test_server, telemetry, top_procs)
    assert len(incidents_second_cycle) == 1
    # Total incidents in DB should remain 1, not duplicate
    assert Incident.objects.filter(server=test_server, category=Incident.Category.CPU).count() == 1


@pytest.mark.django_db
def test_memory_anomaly_detection(test_server, default_threshold_settings):
    telemetry = {
        'cpu': {'cpu_percent': 20.0},
        'memory': {'memory_percent': 89.0, 'swap_percent': 30.0},
        'disk': {'disk_percent': 40.0, 'mountpoint': '/'}
    }
    top_procs = [{'pid': 5678, 'name': 'leak_daemon', 'cpu_percent': 10.0, 'memory_percent': 65.0, 'username': 'root'}]

    incidents = AnomalyDetector.process_system_telemetry(test_server, telemetry, top_procs)
    assert len(incidents) == 1
    inc = incidents[0]
    assert inc.category == Incident.Category.MEMORY
    assert inc.severity in [Incident.Severity.HIGH, Incident.Severity.MEDIUM]
    assert 'leak_daemon' in inc.probable_cause


@pytest.mark.django_db
def test_disk_anomaly_detection(test_server, default_threshold_settings):
    telemetry = {
        'cpu': {'cpu_percent': 15.0},
        'memory': {'memory_percent': 30.0, 'swap_percent': 0.0},
        'disk': {'disk_percent': 92.5, 'mountpoint': '/var'}
    }

    incidents = AnomalyDetector.process_system_telemetry(test_server, telemetry, [])
    assert len(incidents) == 1
    inc = incidents[0]
    assert inc.category == Incident.Category.DISK
    assert inc.severity == Incident.Severity.CRITICAL


@pytest.mark.django_db
def test_stopped_service_anomaly(test_server):
    service_res = {
        'service_name': 'nginx',
        'status': 'INACTIVE',
        'is_active': False,
        'raw_output': 'inactive (dead)'
    }
    inc = AnomalyDetector.process_service_status(test_server, service_res)
    assert inc is not None
    assert inc.category == Incident.Category.SERVICE
    assert inc.severity in [Incident.Severity.HIGH, Incident.Severity.CRITICAL]

    # Now verify recovery clears/resolves the incident
    service_res_recovered = {
        'service_name': 'nginx',
        'status': 'ACTIVE',
        'is_active': True,
        'raw_output': 'active (running)'
    }
    AnomalyDetector.process_service_status(test_server, service_res_recovered)
    inc.refresh_from_db()
    assert inc.status == Incident.Status.RESOLVED
    assert inc.resolved_at is not None


@pytest.mark.django_db
def test_metric_normalization_auto_resolves(test_server, default_threshold_settings):
    # Step 1: Create CPU spike
    high_telemetry = {
        'cpu': {'cpu_percent': 98.0},
        'memory': {'memory_percent': 40.0, 'swap_percent': 0.0},
        'disk': {'disk_percent': 50.0, 'mountpoint': '/'}
    }
    incidents = AnomalyDetector.process_system_telemetry(test_server, high_telemetry, [])
    assert len(incidents) == 1
    cpu_inc = incidents[0]
    assert cpu_inc.status == Incident.Status.OPEN

    # Step 2: Telemetry normalizes (CPU drops to 25%)
    normal_telemetry = {
        'cpu': {'cpu_percent': 25.0},
        'memory': {'memory_percent': 40.0, 'swap_percent': 0.0},
        'disk': {'disk_percent': 50.0, 'mountpoint': '/'}
    }
    AnomalyDetector.process_system_telemetry(test_server, normal_telemetry, [])
    cpu_inc.refresh_from_db()
    assert cpu_inc.status == Incident.Status.RESOLVED
    assert cpu_inc.resolved_at is not None

