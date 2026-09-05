"""
Unit tests for Service Monitor Engine.
"""

from unittest.mock import patch
from monitoring.engines.service_monitor import ServiceMonitor


def test_service_validation():
    # Valid service check
    res = ServiceMonitor.get_service_status('nginx')
    assert 'service_name' in res
    assert res['service_name'] == 'nginx'
    assert res['status'] in ['ACTIVE', 'INACTIVE', 'FAILED', 'NOT_FOUND']


def test_service_invalid_name():
    res = ServiceMonitor.get_service_status('invalid_service_evil')
    assert res['status'] == 'NOT_FOUND'
    assert res['error'] is True


@patch('monitoring.engines.service_monitor.shutil.which')
@patch('monitoring.engines.command_security.CommandSecurity.run_safe_command')
def test_mocked_active_service(mock_cmd, mock_which):
    mock_which.return_value = '/bin/systemctl'
    mock_cmd.return_value = {
        'success': True,
        'stdout': 'active',
        'stderr': '',
        'returncode': 0
    }

    res = ServiceMonitor.get_service_status('nginx')
    assert res['status'] == 'ACTIVE'
    assert res['is_active'] is True


@patch('monitoring.engines.service_monitor.shutil.which')
@patch('monitoring.engines.command_security.CommandSecurity.run_safe_command')
def test_mocked_failed_service(mock_cmd, mock_which):
    mock_which.return_value = '/bin/systemctl'
    mock_cmd.return_value = {
        'success': False,
        'stdout': 'failed',
        'stderr': '',
        'returncode': 3
    }

    res = ServiceMonitor.get_service_status('nginx')
    assert res['status'] == 'FAILED'
    assert res['is_active'] is False
