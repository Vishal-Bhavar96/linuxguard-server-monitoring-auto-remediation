"""
Unit tests for Audit Logging, Models, Views (SSR without JavaScript), and Management Commands.
"""

import pytest
from django.urls import reverse
from monitoring.models import (
    Server, SystemMetric, ProcessMetric, ServiceStatus,
    Incident, RemediationAction, AuditLog, SecurityEvent, SystemSetting
)


@pytest.mark.django_db
def test_models_relationships(test_server, admin_user):
    metric = SystemMetric.objects.create(
        server=test_server,
        cpu_usage=45.2,
        memory_usage=60.1,
        disk_usage=55.0,
        load_average="0.50, 0.45, 0.40"
    )
    assert test_server.system_metrics.count() == 1

    proc = ProcessMetric.objects.create(
        server=test_server,
        pid=1001,
        process_name="nginx",
        cpu_percent=1.5,
        memory_percent=2.0,
        username="www-data",
        status="running"
    )
    assert test_server.process_metrics.count() == 1

    service = ServiceStatus.objects.create(
        server=test_server,
        service_name="nginx",
        status=ServiceStatus.State.ACTIVE
    )
    assert test_server.service_statuses.count() == 1

    audit = AuditLog.objects.create(
        user=admin_user,
        action="SERVER_CHECK",
        resource=f"Server: {test_server.hostname}",
        description="Manual verification test"
    )
    assert AuditLog.objects.count() >= 1


@pytest.mark.django_db
def test_views_ssr_rendering(client, admin_user, test_server):
    # Unauthenticated redirect to login
    resp = client.get(reverse('dashboard'))
    assert resp.status_code == 302
    assert '/login/' in resp.url

    # Authenticate admin
    client.force_login(admin_user)

    # Test Dashboard View
    dash_resp = client.get(reverse('dashboard'))
    assert dash_resp.status_code == 200
    assert b"LinuxGuard" in dash_resp.content
    assert b"<script" not in dash_resp.content  # STRICT REQUIREMENT: No JavaScript!

    # Test Servers List View
    srv_resp = client.get(reverse('server_list'))
    assert srv_resp.status_code == 200
    assert test_server.hostname.encode() in srv_resp.content

    # Test Server Detail View
    det_resp = client.get(reverse('server_detail', kwargs={'server_id': test_server.id}))
    assert det_resp.status_code == 200

    # Test Metrics View
    met_resp = client.get(reverse('metrics'))
    assert met_resp.status_code == 200

    # Test Processes View
    proc_resp = client.get(reverse('processes'))
    assert proc_resp.status_code == 200

    # Test Services View
    svc_resp = client.get(reverse('services'))
    assert svc_resp.status_code == 200

    # Test Incidents View
    inc_resp = client.get(reverse('incident_list'))
    assert inc_resp.status_code == 200

    # Test Remediation View
    rem_resp = client.get(reverse('remediation_list'))
    assert rem_resp.status_code == 200

    # Test Security View
    sec_resp = client.get(reverse('security'))
    assert sec_resp.status_code == 200

    # Test Audit Logs View
    aud_resp = client.get(reverse('audit_logs'))
    assert aud_resp.status_code == 200

    # Test Settings View
    set_resp = client.get(reverse('settings'))
    assert set_resp.status_code == 200


@pytest.mark.django_db
def test_management_commands(test_server):
    from django.core.management import call_command
    # Run seed demo data
    call_command('seed_demo_data')
    assert Server.objects.count() >= 3
    assert Incident.objects.count() >= 1

    # Run single cycle of monitor_server
    call_command('monitor_server', once=True, server_id=test_server.id)
    assert test_server.system_metrics.count() >= 1
