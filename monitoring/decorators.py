"""
Authentication and Role-Based Access Control (RBAC) Decorators.
Supports roles: ADMIN, OPERATOR, VIEWER.
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied


def role_required(allowed_roles):
    """
    Decorator for views that checks whether a user has one of the allowed roles.
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')

            # Superuser has access to everything
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            user_role = getattr(request.user, 'role', None)
            if user_role in allowed_roles:
                return view_func(request, *args, **kwargs)

            messages.error(
                request,
                f"Access Denied: Your role ({request.user.get_role_display() if hasattr(request.user, 'get_role_display') else user_role}) "
                f"does not have permission to access this resource."
            )
            return redirect('dashboard')
        return _wrapped_view
    return decorator


def admin_required(view_func):
    """Convenience decorator requiring ADMIN role."""
    return role_required(['ADMIN'])(view_func)


def operator_required(view_func):
    """Convenience decorator requiring at least OPERATOR role (ADMIN or OPERATOR)."""
    return role_required(['ADMIN', 'OPERATOR'])(view_func)


def viewer_required(view_func):
    """Convenience decorator allowing any authenticated user role."""
    return role_required(['ADMIN', 'OPERATOR', 'VIEWER'])(view_func)
