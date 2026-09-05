"""
Pytest Fixtures for LinuxGuard.
Provides test database setup, mock servers, and RBAC user fixtures.
"""

import pytest
from django.contrib.auth import get_user_model
from monitoring.models import Server, SystemSetting

User = get_user_model()


@pytest.fixture
def admin_user(db):
    user = User.objects.create_user(
        username='test_admin',
        password='AdminPassword123!',
        email='admin@test.local',
        role=User.Role.ADMIN,
        is_staff=True,
        is_superuser=True
    )
    return user


@pytest.fixture
def operator_user(db):
    user = User.objects.create_user(
        username='test_operator',
        password='OperatorPassword123!',
        email='operator@test.local',
        role=User.Role.OPERATOR,
        is_staff=False
    )
    return user


@pytest.fixture
def viewer_user(db):
    user = User.objects.create_user(
        username='test_viewer',
        password='ViewerPassword123!',
        email='viewer@test.local',
        role=User.Role.VIEWER,
        is_staff=False
    )
    return user


@pytest.fixture
def test_server(db):
    server = Server.objects.create(
        hostname='test-ubuntu-node-01',
        ip_address='192.168.1.100',
        operating_system='Ubuntu 22.04 LTS',
        status=Server.Status.ONLINE,
        is_local=True,
        description='Automated Test Target Node'
    )
    return server


@pytest.fixture
def default_threshold_settings(db):
    settings_data = [
        ('CPU_WARN', '85.0', 'CPU Warning Threshold'),
        ('CPU_CRIT', '95.0', 'CPU Critical Threshold'),
        ('RAM_WARN', '85.0', 'RAM Warning Threshold'),
        ('RAM_CRIT', '95.0', 'RAM Critical Threshold'),
        ('DISK_WARN', '80.0', 'Disk Warning Threshold'),
        ('DISK_CRIT', '90.0', 'Disk Critical Threshold'),
        ('SSH_FAIL_LIMIT', '5', 'SSH Limit'),
        ('AUTO_REMEDIATE_SAFE_SERVICES', 'True', 'Auto Remediate Safe Services'),
    ]
    for k, v, d in settings_data:
        SystemSetting.set_setting(k, v, d)
