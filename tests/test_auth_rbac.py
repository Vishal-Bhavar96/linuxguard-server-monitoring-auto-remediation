"""
Unit tests for Authentication and RBAC (ADMIN, OPERATOR, VIEWER).
"""

import pytest
from django.contrib.auth import authenticate
from monitoring.models import User


@pytest.mark.django_db
def test_user_roles_creation(admin_user, operator_user, viewer_user):
    assert admin_user.role == User.Role.ADMIN
    assert admin_user.is_admin_role() is True
    assert admin_user.can_remediate() is True
    assert admin_user.can_approve_remediation() is True

    assert operator_user.role == User.Role.OPERATOR
    assert operator_user.is_operator_role() is True
    assert operator_user.is_admin_role() is False
    assert operator_user.can_remediate() is True
    assert operator_user.can_approve_remediation() is False

    assert viewer_user.role == User.Role.VIEWER
    assert viewer_user.is_viewer_role() is True
    assert viewer_user.can_remediate() is False
    assert viewer_user.can_approve_remediation() is False


@pytest.mark.django_db
def test_user_authentication():
    user = User.objects.create_user(
        username='auth_test_user',
        password='ValidPassword123!',
        role=User.Role.OPERATOR
    )
    # Valid credentials
    authenticated = authenticate(username='auth_test_user', password='ValidPassword123!')
    assert authenticated is not None
    assert authenticated.username == 'auth_test_user'

    # Invalid credentials
    failed_auth = authenticate(username='auth_test_user', password='WrongPassword!')
    assert failed_auth is None
