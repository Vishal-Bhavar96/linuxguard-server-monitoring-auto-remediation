"""
URL Routing for LinuxGuard Platform.
Pure server-side Django routes with no client-side JavaScript routing.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Authentication & User Profile
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),

    # Main Dashboard
    path('', views.dashboard_view, name='dashboard'),
    path('refresh-telemetry/', views.trigger_telemetry_refresh_view, name='refresh_telemetry'),

    # Server Management
    path('servers/', views.server_list_view, name='server_list'),
    path('servers/add/', views.server_create_view, name='server_create'),
    path('servers/<int:server_id>/', views.server_detail_view, name='server_detail'),
    path('servers/<int:server_id>/edit/', views.server_edit_view, name='server_edit'),
    path('servers/<int:server_id>/delete/', views.server_delete_view, name='server_delete'),

    # Telemetry & Metrics
    path('metrics/', views.metrics_view, name='metrics'),
    path('servers/<int:server_id>/metrics/', views.metrics_view, name='server_metrics'),

    # Process Monitoring
    path('processes/', views.processes_view, name='processes'),
    path('servers/<int:server_id>/processes/', views.processes_view, name='server_processes'),

    # Service Monitoring & Actions
    path('services/', views.services_view, name='services'),
    path('servers/<int:server_id>/services/', views.services_view, name='server_services'),
    path('services/action/', views.service_action_view, name='service_action'),

    # Incidents & Root Cause Diagnosis
    path('incidents/', views.incident_list_view, name='incident_list'),
    path('incidents/<int:incident_id>/', views.incident_detail_view, name='incident_detail'),
    path('incidents/<int:incident_id>/update-status/', views.incident_update_status_view, name='incident_update_status'),

    # Remediation Engine & Approvals
    path('remediation/', views.remediation_list_view, name='remediation_list'),
    path('remediation/trigger/', views.remediation_trigger_view, name='remediation_trigger'),
    path('remediation/<int:action_id>/approve/', views.remediation_approve_view, name='remediation_approve'),
    path('remediation/<int:action_id>/reject/', views.remediation_reject_view, name='remediation_reject'),

    # Security & Audit Logs
    path('security/', views.security_view, name='security'),
    path('audit/', views.audit_log_view, name='audit_logs'),

    # Platform Settings
    path('settings/', views.settings_view, name='settings'),
]
