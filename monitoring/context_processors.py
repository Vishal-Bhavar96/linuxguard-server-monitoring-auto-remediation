"""
Global Context Processor for LinuxGuard Navigation and System Badges.
Provides metrics counters without running any client-side JavaScript.
"""

from .models import Incident, Server, SecurityEvent, RemediationAction


def global_navigation_context(request):
    """
    Supplies global counts for the top navigation bar and sidebar.
    """
    if not request.user.is_authenticated:
        return {}

    try:
        open_incidents_count = Incident.objects.filter(
            status__in=[Incident.Status.OPEN, Incident.Status.INVESTIGATING]
        ).count()

        critical_incidents_count = Incident.objects.filter(
            status__in=[Incident.Status.OPEN, Incident.Status.INVESTIGATING],
            severity=Incident.Severity.CRITICAL
        ).count()

        pending_remediations_count = RemediationAction.objects.filter(
            status=RemediationAction.Status.PENDING_APPROVAL
        ).count()

        recent_security_alerts_count = SecurityEvent.objects.filter(
            severity__in=[SecurityEvent.Severity.HIGH, SecurityEvent.Severity.CRITICAL]
        ).count()

        total_servers_count = Server.objects.count()
        healthy_servers_count = Server.objects.filter(status=Server.Status.ONLINE).count()

        user_role = getattr(request.user, 'role', 'VIEWER')
        can_approve = request.user.is_superuser or user_role == 'ADMIN'
        can_remediate = request.user.is_superuser or user_role in ['ADMIN', 'OPERATOR']

        return {
            'nav_open_incidents': open_incidents_count,
            'nav_critical_incidents': critical_incidents_count,
            'nav_pending_remediations': pending_remediations_count,
            'nav_security_alerts': recent_security_alerts_count,
            'nav_total_servers': total_servers_count,
            'nav_healthy_servers': healthy_servers_count,
            'user_role': user_role,
            'user_can_approve': can_approve,
            'user_can_remediate': can_remediate,
        }
    except Exception:
        # Failsafe during initial migrations or setup
        return {}
