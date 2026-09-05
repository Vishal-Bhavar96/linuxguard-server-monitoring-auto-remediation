"""
Unit tests for Command Security, Allowlisting, and Remediation Engine.
"""

import pytest
from unittest.mock import patch
from monitoring.models import Incident, RemediationAction, AuditLog
from monitoring.engines.command_security import CommandSecurity, CommandSecurityError
from monitoring.engines.remediation_engine import RemediationEngine


def test_allowed_service_validation():
    assert CommandSecurity.validate_service_name('nginx') == 'nginx'
    assert CommandSecurity.validate_service_name('docker') == 'docker'
    assert CommandSecurity.validate_service_name('ssh') == 'ssh'

    with pytest.raises(CommandSecurityError):
        CommandSecurity.validate_service_name('malicious_daemon; rm -rf /')


def test_forbidden_command_prevention():
    # Attempting to construct dangerous command
    with pytest.raises(CommandSecurityError):
        CommandSecurity.run_safe_command(['rm', '-rf', '/var/log'])

    with pytest.raises(CommandSecurityError):
        CommandSecurity.run_safe_command(['reboot'])

    with pytest.raises(CommandSecurityError):
        CommandSecurity.run_safe_command(['shutdown', '-h', 'now'])

    with pytest.raises(CommandSecurityError):
        CommandSecurity.run_safe_command(['kill', '-9', '1234'])


def test_safe_command_building():
    cmd = CommandSecurity.build_safe_command('systemctl_status', service='nginx')
    assert cmd == ['systemctl', 'status', 'nginx']


@pytest.mark.django_db
def test_remediation_workflow_success(test_server, operator_user):
    incident = Incident.objects.create(
        server=test_server,
        title="Service 'nginx' stopped",
        category=Incident.Category.SERVICE,
        severity=Incident.Severity.HIGH,
        status=Incident.Status.OPEN
    )

    action = RemediationEngine.create_remediation_action(
        incident=incident,
        action_name="Auto Restart nginx",
        command_type="RESTART_SERVICE",
        requires_approval=False,
        user=operator_user
    )

    assert action.status == RemediationAction.Status.APPROVED
    assert AuditLog.objects.filter(action="REMEDIATION_CREATED").exists()

    # Execute with mock success
    res = RemediationEngine.execute_service_restart(
        remediation_action=action,
        service_name='nginx',
        executor_user=operator_user,
        mock_success=True
    )

    assert res['success'] is True
    action.refresh_from_db()
    incident.refresh_from_db()

    assert action.status == RemediationAction.Status.SUCCESS
    assert incident.status == Incident.Status.RESOLVED
    assert incident.resolved_at is not None
    assert AuditLog.objects.filter(action="REMEDIATION_SUCCESS").exists()
