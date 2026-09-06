"""
Unit tests for Auto-Remediation Workflow and Post-Execution Verification.
"""

import pytest
from monitoring.models import Incident, RemediationAction, AuditLog
from monitoring.engines.remediation_engine import RemediationEngine


@pytest.mark.django_db
def test_remediation_workflow_success_verification(test_server, operator_user):
    # 1. Create an incident
    incident = Incident.objects.create(
        server=test_server,
        title="Service 'nginx' is FAILED on host",
        description="Nginx daemon crash detected",
        category=Incident.Category.SERVICE,
        severity=Incident.Severity.CRITICAL,
        status=Incident.Status.OPEN
    )

    # 2. Create remediation action
    action = RemediationEngine.create_remediation_action(
        incident=incident,
        action_name="Auto Restart: nginx",
        command_type="RESTART_SERVICE",
        requires_approval=False,
        user=operator_user
    )
    assert action.status == RemediationAction.Status.APPROVED

    # 3. Execute with mock success verification
    result = RemediationEngine.execute_service_restart(
        remediation_action=action,
        service_name="nginx",
        executor_user=operator_user,
        mock_success=True
    )

    assert result['success'] is True
    assert result['verified_active'] is True

    action.refresh_from_db()
    incident.refresh_from_db()

    assert action.status == RemediationAction.Status.SUCCESS
    assert incident.status == Incident.Status.RESOLVED
    assert incident.resolved_at is not None

    # Check AuditLog
    assert AuditLog.objects.filter(action="REMEDIATION_SUCCESS").exists()


@pytest.mark.django_db
def test_remediation_workflow_failure_verification(test_server, operator_user):
    # 1. Create an incident
    incident = Incident.objects.create(
        server=test_server,
        title="Service 'docker' is FAILED on host",
        description="Docker daemon crash detected",
        category=Incident.Category.SERVICE,
        severity=Incident.Severity.CRITICAL,
        status=Incident.Status.OPEN
    )

    # 2. Create remediation action
    action = RemediationEngine.create_remediation_action(
        incident=incident,
        action_name="Auto Restart: docker",
        command_type="RESTART_SERVICE",
        requires_approval=False,
        user=operator_user
    )

    # 3. Execute with mock failure (mock_success=False)
    result = RemediationEngine.execute_service_restart(
        remediation_action=action,
        service_name="docker",
        executor_user=operator_user,
        mock_success=False
    )

    action.refresh_from_db()
    incident.refresh_from_db()

    assert action.status == RemediationAction.Status.FAILED
    assert incident.status == Incident.Status.INVESTIGATING
    assert AuditLog.objects.filter(action="REMEDIATION_FAILED").exists()
