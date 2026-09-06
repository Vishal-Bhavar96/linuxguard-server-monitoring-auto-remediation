"""
Django Views for LinuxGuard Platform.
Server-Side Rendered (SSR) views using pure HTML5 and CSS3 without JavaScript.
"""

from datetime import timedelta
import socket
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Avg, Max, Min, Count
from django.core.paginator import Paginator

from .models import (
    User, Server, SystemMetric, ProcessMetric, ServiceStatus,
    Incident, RemediationAction, AuditLog, SecurityEvent, SystemSetting
)
from .forms import (
    ServerForm, IncidentFilterForm, ProcessFilterForm,
    RemediationTriggerForm, SettingsConfigForm, AuditFilterForm
)
from .decorators import role_required, admin_required, operator_required, viewer_required
from .engines.system_monitor import SystemMonitor
from .engines.process_monitor import ProcessMonitor
from .engines.service_monitor import ServiceMonitor
from .engines.disk_monitor import DiskMonitor
from .engines.network_monitor import NetworkMonitor
from .engines.ssh_monitor import SSHMonitor
from .engines.anomaly_detector import AnomalyDetector
from .engines.remediation_engine import RemediationEngine
from .engines.command_security import CommandSecurity, CommandSecurityError


# ==============================================================================
# 1. AUTHENTICATION VIEWS
# ==============================================================================

@csrf_protect
def login_view(request):

    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        u = request.POST.get('username', '').strip()
        p = request.POST.get('password', '')
        user = authenticate(request, username=u, password=p)

        if user is not None:
            if user.is_active:
                auth_login(request, user)
                AuditLog.objects.create(
                    user=user,
                    action="USER_LOGIN",
                    resource="Auth Session",
                    description=f"User '{user.username}' logged in successfully.",
                    ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1')
                )
                messages.success(request, f"Welcome back, {user.username}!")
                next_url = request.GET.get('next') or 'dashboard'
                return redirect(next_url)
            else:
                messages.error(request, "This account is disabled. Contact your administrator.")
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'auth/login.html')


@login_required
def logout_view(request):
    user = request.user
    AuditLog.objects.create(
        user=user,
        action="USER_LOGOUT",
        resource="Auth Session",
        description=f"User '{user.username}' logged out.",
        ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1')
    )
    auth_logout(request)
    messages.info(request, "You have been securely logged out.")
    return redirect('login')


@login_required
def profile_view(request):
    return render(request, 'auth/profile.html', {'user': request.user})


# ==============================================================================
# 2. MAIN DASHBOARD VIEW
# ==============================================================================

@login_required
def dashboard_view(request):
    """
    Enterprise Linux Operations Command Center.
    Visualized with pure CSS gauges, cards, and tables.
    """
    servers = Server.objects.all()
    host_info = SystemMonitor.get_host_info()

    if not servers.exists():
        # Ensure local server exists with real detected metadata
        s_local = Server.objects.create(
            hostname=host_info['hostname'],
            ip_address=host_info['ip_address'],
            operating_system=host_info['operating_system'],
            kernel_version=host_info.get('kernel_version', ''),
            status=Server.Status.ONLINE,
            is_local=True,
            description='Primary Local Host Machine'
        )
        servers = Server.objects.all()

    # Active Server Selection
    selected_server_id = request.GET.get('server_id')
    if selected_server_id:
        current_server = get_object_or_404(Server, id=selected_server_id)
    else:
        current_server = servers.filter(is_local=True).first() or servers.first()

    # Sync local server metadata if currently viewing local node
    if current_server and current_server.is_local:
        current_server.operating_system = host_info['operating_system']
        current_server.kernel_version = host_info.get('kernel_version', '')
        current_server.ip_address = host_info['ip_address']
        current_server.last_seen = timezone.now()
        current_server.save()

    # Telemetry snapshot for current server
    latest_metric = None
    if current_server:
        latest_metric = current_server.system_metrics.order_by('-timestamp').first()

    # Real-time quick snapshot if local host
    live_telemetry = None
    if current_server and current_server.is_local:
        live_telemetry = SystemMonitor.collect_snapshot()

    # Overview KPI Metrics (8 Standard Cards)
    total_servers = servers.count()
    healthy_servers = servers.filter(status=Server.Status.ONLINE).count()
    online_servers = servers.filter(status=Server.Status.ONLINE).count()
    offline_servers = servers.filter(status=Server.Status.OFFLINE).count()
    degraded_servers = servers.filter(status=Server.Status.DEGRADED).count()
    critical_servers = servers.filter(status=Server.Status.CRITICAL).count()

    active_incidents = Incident.objects.filter(status__in=[Incident.Status.OPEN, Incident.Status.INVESTIGATING])
    critical_incidents_count = active_incidents.filter(severity=Incident.Severity.CRITICAL).count()
    recent_incidents = Incident.objects.select_related('server').order_by('-detected_at')[:6]

    security_events_count = SecurityEvent.objects.count()
    recent_security_events = SecurityEvent.objects.select_related('server').order_by('-timestamp')[:5]

    pending_remediations_count = RemediationAction.objects.filter(status=RemediationAction.Status.PENDING_APPROVAL).count()
    recent_remediations = RemediationAction.objects.select_related('incident', 'incident__server').order_by('-id')[:5]

    # Services status on current server
    services = ServiceStatus.objects.filter(server=current_server) if current_server else []

    context = {
        'servers': servers,
        'current_server': current_server,
        'latest_metric': latest_metric,
        'live_telemetry': live_telemetry,
        'host_info': host_info,
        'is_linux': host_info.get('is_linux', False),
        # 8 KPI Metrics
        'total_servers': total_servers,
        'healthy_servers': healthy_servers,
        'online_servers': online_servers,
        'offline_servers': offline_servers,
        'degraded_servers': degraded_servers,
        'critical_servers': critical_servers,
        'active_incidents_count': active_incidents.count(),
        'critical_incidents_count': critical_incidents_count,
        'security_events_count': security_events_count,
        'pending_remediations_count': pending_remediations_count,
        # Recent Data Feeds
        'recent_incidents': recent_incidents,
        'recent_security_events': recent_security_events,
        'recent_remediations': recent_remediations,
        'services': services,
    }
    return render(request, 'dashboard/index.html', context)


@login_required
@operator_required
def trigger_telemetry_refresh_view(request):
    """
    Manually triggers immediate telemetry sampling on the host server.
    """
    host_info = SystemMonitor.get_host_info()
    server, _ = Server.objects.get_or_create(
        is_local=True,
        defaults={
            'hostname': host_info['hostname'],
            'ip_address': host_info['ip_address'],
            'operating_system': host_info['operating_system'],
            'kernel_version': host_info.get('kernel_version', ''),
            'status': Server.Status.ONLINE,
        }
    )
    server.operating_system = host_info['operating_system']
    server.kernel_version = host_info.get('kernel_version', '')
    server.ip_address = host_info['ip_address']
    server.last_seen = timezone.now()
    server.save()

    # Sample telemetry
    telemetry = SystemMonitor.collect_snapshot()
    top_procs = ProcessMonitor.get_top_processes(limit=5, sort_by='cpu')

    # Save metric
    SystemMetric.objects.create(
        server=server,
        cpu_usage=telemetry['cpu']['cpu_percent'],
        memory_usage=telemetry['memory']['memory_percent'],
        disk_usage=telemetry['disk']['disk_percent'],
        network_sent=telemetry['network']['bytes_sent'],
        network_received=telemetry['network']['bytes_recv'],
        load_average=telemetry['load_average']['formatted'],
        timestamp=timezone.now()
    )

    # Save top process telemetry
    for proc in top_procs:
        ProcessMetric.objects.create(
            server=server,
            pid=proc['pid'],
            process_name=proc['name'],
            cpu_percent=proc['cpu_percent'],
            memory_percent=proc['memory_percent'],
            username=proc['username'],
            status=proc['status'],
            timestamp=timezone.now()
        )

    # Check services
    services_res = ServiceMonitor.check_all_services()
    for s in services_res:
        ServiceStatus.objects.update_or_create(
            server=server,
            service_name=s['service_name'],
            defaults={'status': s['status'], 'checked_at': timezone.now()}
        )

    # Detect anomalies & auto-resolution
    incidents = AnomalyDetector.process_system_telemetry(server, telemetry, top_procs)
    for s in services_res:
        serv_inc = AnomalyDetector.process_service_status(server, s)
        if serv_inc:
            incidents.append(serv_inc)

    AuditLog.objects.create(
        user=request.user,
        action="TELEMETRY_REFRESH",
        resource=f"Server: {server.hostname}",
        description=f"Host telemetry snapshot refreshed. Recorded CPU: {telemetry['cpu']['cpu_percent']}%, RAM: {telemetry['memory']['memory_percent']}%, Disk: {telemetry['disk']['disk_percent']}%.",
        ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1')
    )

    messages.success(request, f"Host telemetry updated for {server.hostname}! (CPU: {telemetry['cpu']['cpu_percent']}%, RAM: {telemetry['memory']['memory_percent']}%, Disk: {telemetry['disk']['disk_percent']}%)")
    return redirect(request.META.get('HTTP_REFERER') or 'dashboard')


# ==============================================================================
# 3. SERVER MANAGEMENT VIEWS
# ==============================================================================

@login_required
def server_list_view(request):
    servers = Server.objects.annotate(
        metric_count=Count('system_metrics'),
        open_incident_count=Count('incidents', filter=Q(incidents__status__in=[Incident.Status.OPEN, Incident.Status.INVESTIGATING]))
    ).order_by('-is_local', 'hostname')

    return render(request, 'servers/list.html', {'servers': servers})


@login_required
def server_detail_view(request, server_id):
    server = get_object_or_404(Server, id=server_id)
    latest_metrics = server.system_metrics.order_by('-timestamp')[:20]
    latest_metric = latest_metrics.first()
    services = server.service_statuses.all()
    incidents = server.incidents.order_by('-detected_at')[:10]
    security_events = server.security_events.order_by('-timestamp')[:10]
    recent_processes = server.process_metrics.order_by('-timestamp', '-cpu_percent')[:10]

    # Aggregate stats demonstration (AVG, MAX, MIN)
    agg_stats = server.system_metrics.aggregate(
        avg_cpu=Avg('cpu_usage'),
        max_cpu=Max('cpu_usage'),
        min_cpu=Min('cpu_usage'),
        avg_ram=Avg('memory_usage'),
        max_ram=Max('memory_usage'),
        avg_disk=Avg('disk_usage'),
    )

    recent_audit_logs = AuditLog.objects.filter(
        Q(resource__icontains=server.hostname) | Q(description__icontains=server.hostname)
    ).order_by('-timestamp')[:10]

    uptime_str = "Active"
    if server.is_local:
        uptime_str = SystemMonitor.get_uptime()['formatted']

    context = {
        'server': server,
        'latest_metric': latest_metric,
        'latest_metrics': latest_metrics,
        'services': services,
        'incidents': incidents,
        'security_events': security_events,
        'recent_processes': recent_processes,
        'recent_audit_logs': recent_audit_logs,
        'uptime_str': uptime_str,
        'agg_stats': agg_stats,
    }
    return render(request, 'servers/detail.html', context)


@login_required
@admin_required
def server_create_view(request):
    if request.method == 'POST':
        form = ServerForm(request.POST)
        if form.is_valid():
            server = form.save()
            AuditLog.objects.create(
                user=request.user,
                action="SERVER_CREATED",
                resource=f"Server: {server.hostname}",
                description=f"Added new server {server.hostname} ({server.ip_address}).",
                ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1')
            )
            messages.success(request, f"Server '{server.hostname}' added successfully.")
            return redirect('server_detail', server_id=server.id)
    else:
        form = ServerForm()

    return render(request, 'servers/form.html', {'form': form, 'title': 'Register Monitored Server'})


@login_required
@admin_required
def server_edit_view(request, server_id):
    server = get_object_or_404(Server, id=server_id)
    if request.method == 'POST':
        form = ServerForm(request.POST, instance=server)
        if form.is_valid():
            server = form.save()
            AuditLog.objects.create(
                user=request.user,
                action="SERVER_UPDATED",
                resource=f"Server: {server.hostname}",
                description=f"Updated configuration for server {server.hostname}.",
                ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1')
            )
            messages.success(request, f"Server '{server.hostname}' updated successfully.")
            return redirect('server_detail', server_id=server.id)
    else:
        form = ServerForm(instance=server)

    return render(request, 'servers/form.html', {'form': form, 'server': server, 'title': f'Edit Server: {server.hostname}'})


@login_required
@admin_required
def server_delete_view(request, server_id):
    server = get_object_or_404(Server, id=server_id)
    if request.method == 'POST':
        hostname = server.hostname
        server.delete()
        AuditLog.objects.create(
            user=request.user,
            action="SERVER_DELETED",
            resource=f"Server: {hostname}",
            description=f"Removed server {hostname} from platform monitoring.",
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1')
        )
        messages.success(request, f"Server '{hostname}' deleted.")
        return redirect('server_list')

    return render(request, 'servers/delete_confirm.html', {'server': server})


# ==============================================================================
# 4. METRICS & TELEMETRY VIEW
# ==============================================================================

@login_required
def metrics_view(request, server_id=None):
    servers = Server.objects.all()
    if server_id:
        selected_server = get_object_or_404(Server, id=server_id)
    else:
        selected_server = servers.filter(is_local=True).first() or servers.first()

    metrics = []
    agg = {}
    if selected_server:
        metrics_qs = selected_server.system_metrics.order_by('-timestamp')
        paginator = Paginator(metrics_qs, 25)
        page_number = request.GET.get('page')
        metrics = paginator.get_page(page_number)

        agg = selected_server.system_metrics.aggregate(
            avg_cpu=Avg('cpu_usage'),
            max_cpu=Max('cpu_usage'),
            avg_ram=Avg('memory_usage'),
            max_ram=Max('memory_usage'),
            avg_disk=Avg('disk_usage'),
            max_disk=Max('disk_usage'),
        )

    # Disk partitions and network overview
    disk_report = DiskMonitor.get_disk_report()
    network_report = NetworkMonitor.get_network_overview()

    context = {
        'servers': servers,
        'selected_server': selected_server,
        'metrics': metrics,
        'agg': agg,
        'disk_report': disk_report,
        'network_report': network_report,
    }
    return render(request, 'metrics/index.html', context)


# ==============================================================================
# 5. PROCESS MONITORING VIEW
# ==============================================================================

@login_required
def processes_view(request, server_id=None):
    servers = Server.objects.all()
    if server_id:
        selected_server = get_object_or_404(Server, id=server_id)
    else:
        selected_server = servers.filter(is_local=True).first() or servers.first()

    form = ProcessFilterForm(request.GET)
    sort_by = request.GET.get('sort_by', 'cpu')
    search_query = request.GET.get('search', '').strip()

    processes = []
    if selected_server and selected_server.is_local:
        # Real host live processes
        processes = ProcessMonitor.get_top_processes(limit=30, sort_by=sort_by, filter_name=search_query)
    elif selected_server:
        # DB recorded process metrics
        qs = selected_server.process_metrics.order_by('-timestamp')
        if search_query:
            qs = qs.filter(Q(process_name__icontains=search_query) | Q(username__icontains=search_query))
        if sort_by == 'memory':
            qs = qs.order_by('-memory_percent')
        elif sort_by == 'pid':
            qs = qs.order_by('pid')
        elif sort_by == 'name':
            qs = qs.order_by('process_name')
        else:
            qs = qs.order_by('-cpu_percent')

        for p in qs[:30]:
            processes.append({
                'pid': p.pid,
                'name': p.process_name,
                'cpu_percent': p.cpu_percent,
                'memory_percent': p.memory_percent,
                'username': p.username,
                'status': p.status,
            })

    context = {
        'servers': servers,
        'selected_server': selected_server,
        'processes': processes,
        'form': form,
        'sort_by': sort_by,
        'search_query': search_query,
    }
    return render(request, 'processes/index.html', context)


# ==============================================================================
# 6. SERVICE MONITORING & ACTIONS VIEW
# ==============================================================================

@login_required
def services_view(request, server_id=None):
    servers = Server.objects.all()
    if server_id:
        selected_server = get_object_or_404(Server, id=server_id)
    else:
        selected_server = servers.filter(is_local=True).first() or servers.first()

    services_data = []
    if selected_server and selected_server.is_local:
        # Check live service state
        services_data = ServiceMonitor.check_all_services()
    elif selected_server:
        db_services = selected_server.service_statuses.all()
        for s in db_services:
            services_data.append({
                'service_name': s.service_name,
                'status': s.status,
                'is_active': s.status == ServiceStatus.State.ACTIVE,
                'checked_at': s.checked_at,
            })

    context = {
        'servers': servers,
        'selected_server': selected_server,
        'services': services_data,
    }
    return render(request, 'services/index.html', context)


@login_required
@operator_required
def service_action_view(request):
    """
    Handles safe service operations: restart, status check, or log retrieval via POST.
    """
    if request.method != 'POST':
        return redirect('services')

    action = request.POST.get('action')
    service_name = request.POST.get('service_name', '').strip()
    server_id = request.POST.get('server_id')

    try:
        valid_service = CommandSecurity.validate_service_name(service_name)
    except CommandSecurityError as e:
        messages.error(request, f"Security Violation: {str(e)}")
        return redirect('services')

    server = Server.objects.filter(id=server_id).first() or Server.objects.filter(is_local=True).first()

    if action == 'restart':
        if not request.user.can_remediate():
            messages.error(request, "Permission Denied: Only Operators and Admins can restart services.")
            return redirect('services')

        cmd = ['systemctl', 'restart', valid_service]
        res = CommandSecurity.run_safe_command(cmd, timeout=30)

        # Update service status in DB
        verify_status = ServiceMonitor.get_service_status(valid_service)
        if server:
            ServiceStatus.objects.update_or_create(
                server=server,
                service_name=valid_service,
                defaults={'status': verify_status['status'], 'checked_at': timezone.now()}
            )

        AuditLog.objects.create(
            user=request.user,
            action="SERVICE_RESTARTED",
            resource=f"Service: {valid_service} on {server.hostname if server else 'Local'}",
            description=f"Operator executed safe service restart for '{valid_service}'. Result: {verify_status['status']}.",
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1')
        )

        if verify_status['is_active']:
            messages.success(request, f"Service '{valid_service}' successfully restarted and confirmed ACTIVE.")
        else:
            messages.warning(request, f"Restart triggered for '{valid_service}'. Current state: {verify_status['status']}.")

    elif action == 'check':
        res = ServiceMonitor.get_service_status(valid_service)
        if server:
            ServiceStatus.objects.update_or_create(
                server=server,
                service_name=valid_service,
                defaults={'status': res['status'], 'checked_at': timezone.now()}
            )
        messages.info(request, f"Service '{valid_service}' status: {res['status']}.")

    elif action == 'logs':
        log_res = ServiceMonitor.get_service_logs(valid_service, lines=30)
        request.session['service_log_view'] = {
            'service': valid_service,
            'logs': log_res['stdout'] or log_res['stderr'] or 'No logs available.'
        }
        return redirect('services')

    return redirect('services')


# ==============================================================================
# 7. INCIDENTS & ROOT CAUSE ANALYSIS VIEWS
# ==============================================================================

@login_required
def incident_list_view(request):
    form = IncidentFilterForm(request.GET)
    incidents = Incident.objects.select_related('server').order_by('-detected_at')

    if form.is_valid():
        if form.cleaned_data.get('server'):
            incidents = incidents.filter(server=form.cleaned_data['server'])
        if form.cleaned_data.get('severity'):
            incidents = incidents.filter(severity=form.cleaned_data['severity'])
        if form.cleaned_data.get('status'):
            incidents = incidents.filter(status=form.cleaned_data['status'])
        if form.cleaned_data.get('category'):
            incidents = incidents.filter(category=form.cleaned_data['category'])

    paginator = Paginator(incidents, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Incident summary statistics
    stats = {
        'total': Incident.objects.count(),
        'open': Incident.objects.filter(status=Incident.Status.OPEN).count(),
        'investigating': Incident.objects.filter(status=Incident.Status.INVESTIGATING).count(),
        'resolved': Incident.objects.filter(status=Incident.Status.RESOLVED).count(),
        'critical': Incident.objects.filter(severity=Incident.Severity.CRITICAL, status__in=[Incident.Status.OPEN, Incident.Status.INVESTIGATING]).count(),
    }

    return render(request, 'incidents/list.html', {'form': form, 'incidents': page_obj, 'stats': stats})


@login_required
def incident_detail_view(request, incident_id):
    incident = get_object_or_404(Incident.objects.select_related('server'), id=incident_id)
    remediation_actions = incident.remediation_actions.select_related('approved_by').order_by('-id')
    remediation_form = RemediationTriggerForm()

    context = {
        'incident': incident,
        'remediation_actions': remediation_actions,
        'remediation_form': remediation_form,
    }
    return render(request, 'incidents/detail.html', context)


@login_required
@operator_required
def incident_update_status_view(request, incident_id):
    if request.method != 'POST':
        return redirect('incident_detail', incident_id=incident_id)

    incident = get_object_or_404(Incident, id=incident_id)
    new_status = request.POST.get('status')

    if new_status in dict(Incident.Status.choices):
        old_status = incident.status
        incident.status = new_status
        if new_status == Incident.Status.RESOLVED and not incident.resolved_at:
            incident.resolved_at = timezone.now()
        elif new_status != Incident.Status.RESOLVED:
            incident.resolved_at = None
        incident.save()

        AuditLog.objects.create(
            user=request.user,
            action="INCIDENT_STATUS_UPDATED",
            resource=f"Incident #{incident.id}",
            description=f"Status changed from {old_status} to {new_status} by {request.user.username}.",
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1')
        )
        messages.success(request, f"Incident #{incident.id} status updated to {incident.get_status_display()}.")

    return redirect('incident_detail', incident_id=incident.id)


# ==============================================================================
# 8. REMEDIATION ENGINE & APPROVALS VIEWS
# ==============================================================================

@login_required
def remediation_list_view(request):
    actions = RemediationAction.objects.select_related('incident', 'incident__server', 'approved_by').order_by('-id')
    pending_actions = actions.filter(status=RemediationAction.Status.PENDING_APPROVAL)
    executed_actions = actions.exclude(status=RemediationAction.Status.PENDING_APPROVAL)

    trigger_form = RemediationTriggerForm()

    context = {
        'pending_actions': pending_actions,
        'executed_actions': executed_actions,
        'trigger_form': trigger_form,
    }
    return render(request, 'remediation/list.html', context)


@login_required
@operator_required
def remediation_trigger_view(request):
    """
    Creates and initiates a safe remediation action linked to an incident.
    """
    if request.method != 'POST':
        return redirect('remediation_list')

    form = RemediationTriggerForm(request.POST)
    incident_id = request.POST.get('incident_id')

    if form.is_valid():
        action_type = form.cleaned_data['action_type']
        service_name = form.cleaned_data['service_name']
        reason = form.cleaned_data['reason']

        incident = None
        if incident_id:
            incident = Incident.objects.filter(id=incident_id).first()

        if not incident:
            # Create a general incident placeholder for manual remediation
            server = Server.objects.filter(is_local=True).first() or Server.objects.first()
            incident = Incident.objects.create(
                server=server,
                title=f"Manual Remediation: {action_type} ({service_name or 'System'})",
                description=f"Manual remediation requested by {request.user.username}. Reason: {reason}",
                category=Incident.Category.SYSTEM,
                severity=Incident.Severity.MEDIUM,
                status=Incident.Status.INVESTIGATING
            )

        # Build action
        action_name = f"{action_type.replace('_', ' ').title()}: {service_name or 'System'}"
        rem_action = RemediationEngine.create_remediation_action(
            incident=incident,
            action_name=action_name,
            command_type=action_type,
            requires_approval=not request.user.can_approve_remediation(),
            user=request.user
        )

        # If user has auto-approval rights, execute immediately
        if request.user.can_approve_remediation():
            if action_type == 'RESTART_SERVICE':
                res = RemediationEngine.execute_service_restart(rem_action, service_name, request.user)
            elif action_type == 'COLLECT_SERVICE_LOGS':
                res = RemediationEngine.execute_diagnostic_log_collection(rem_action, service_name, request.user)
            else:
                rem_action.status = RemediationAction.Status.SUCCESS
                rem_action.result = f"Safe operation '{action_type}' executed."
                rem_action.executed_at = timezone.now()
                rem_action.save()
            messages.success(request, f"Remediation '{action_name}' executed successfully.")
        else:
            messages.info(request, f"Remediation '{action_name}' registered and queued for Administrator approval.")

    return redirect('remediation_list')


@login_required
@admin_required
def remediation_approve_view(request, action_id):
    if request.method != 'POST':
        return redirect('remediation_list')

    action = get_object_or_404(RemediationAction, id=action_id)
    service_name = request.POST.get('service_name') or 'nginx'

    RemediationEngine.approve_and_execute(action, request.user, service_name)
    messages.success(request, f"Remediation #{action.id} approved and executed.")
    return redirect('remediation_list')


@login_required
@admin_required
def remediation_reject_view(request, action_id):
    if request.method != 'POST':
        return redirect('remediation_list')

    action = get_object_or_404(RemediationAction, id=action_id)
    action.status = RemediationAction.Status.REJECTED
    action.save()

    AuditLog.objects.create(
        user=request.user,
        action="REMEDIATION_REJECTED",
        resource=f"Remediation #{action.id}",
        description=f"Administrator '{request.user.username}' rejected remediation '{action.action_name}'.",
        ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1')
    )
    messages.warning(request, f"Remediation #{action.id} was rejected.")
    return redirect('remediation_list')


# ==============================================================================
# 9. SECURITY & AUDIT VIEWS
# ==============================================================================

@login_required
def security_view(request):
    events = SecurityEvent.objects.select_related('server').order_by('-timestamp')
    brute_force_events = events.filter(event_type=SecurityEvent.EventType.SSH_BRUTE_FORCE)

    # Top attacking IPs demonstration (GROUP BY / COUNT)
    top_ips = SecurityEvent.objects.filter(
        source_ip__gt=''
    ).values('source_ip').annotate(
        attack_count=Count('id'),
        latest_attack=Max('timestamp')
    ).order_by('-attack_count')[:10]

    paginator = Paginator(events, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'events': page_obj,
        'brute_force_count': brute_force_events.count(),
        'high_severity_count': events.filter(severity__in=[SecurityEvent.Severity.HIGH, SecurityEvent.Severity.CRITICAL]).count(),
        'top_ips': top_ips,
    }
    return render(request, 'security/index.html', context)


@login_required
def audit_log_view(request):
    form = AuditFilterForm(request.GET)
    logs = AuditLog.objects.select_related('user').order_by('-timestamp')

    if form.is_valid():
        search = form.cleaned_data.get('search')
        action = form.cleaned_data.get('action')
        if search:
            logs = logs.filter(
                Q(description__icontains=search) |
                Q(resource__icontains=search) |
                Q(user__username__icontains=search)
            )
        if action:
            logs = logs.filter(action__icontains=action)

    paginator = Paginator(logs, 30)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'audit/index.html', {'logs': page_obj, 'form': form})


# ==============================================================================
# 10. PLATFORM SETTINGS VIEW
# ==============================================================================

@login_required
def settings_view(request):
    defaults = AnomalyDetector.get_thresholds()

    if request.method == 'POST':
        if not request.user.is_admin_role():
            messages.error(request, "Permission Denied: Only Administrators can modify platform settings.")
            return redirect('settings')

        form = SettingsConfigForm(request.POST)
        if form.is_valid():
            SystemSetting.set_setting('CPU_WARN', form.cleaned_data['cpu_warn'], 'CPU Warning Threshold (%)')
            SystemSetting.set_setting('CPU_CRIT', form.cleaned_data['cpu_crit'], 'CPU Critical Threshold (%)')
            SystemSetting.set_setting('RAM_WARN', form.cleaned_data['ram_warn'], 'RAM Warning Threshold (%)')
            SystemSetting.set_setting('RAM_CRIT', form.cleaned_data['ram_crit'], 'RAM Critical Threshold (%)')
            SystemSetting.set_setting('DISK_WARN', form.cleaned_data['disk_warn'], 'Disk Warning Threshold (%)')
            SystemSetting.set_setting('DISK_CRIT', form.cleaned_data['disk_crit'], 'Disk Critical Threshold (%)')
            SystemSetting.set_setting('SSH_FAIL_LIMIT', form.cleaned_data['ssh_fail_limit'], 'SSH Brute-Force Alert Threshold')
            SystemSetting.set_setting('SSH_WINDOW_MINUTES', form.cleaned_data['ssh_window_minutes'], 'SSH Detection Window (Minutes)')
            SystemSetting.set_setting('AUTO_REMEDIATE_SAFE_SERVICES', str(form.cleaned_data['auto_remediate_safe_services']), 'Auto-restart safe stopped services')

            AuditLog.objects.create(
                user=request.user,
                action="SETTINGS_UPDATED",
                resource="System Settings",
                description="Platform anomaly thresholds and auto-remediation policies updated.",
                ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1')
            )
            messages.success(request, "Threshold configurations updated successfully.")
            return redirect('settings')
    else:
        initial_data = {
            'cpu_warn': defaults['cpu_warn'],
            'cpu_crit': defaults['cpu_crit'],
            'ram_warn': defaults['ram_warn'],
            'ram_crit': defaults['ram_crit'],
            'disk_warn': defaults['disk_warn'],
            'disk_crit': defaults['disk_crit'],
            'ssh_fail_limit': defaults['ssh_limit'],
            'ssh_window_minutes': int(SystemSetting.get_setting('SSH_WINDOW_MINUTES', '10')),
            'auto_remediate_safe_services': SystemSetting.get_setting('AUTO_REMEDIATE_SAFE_SERVICES', 'True').lower() in ('true', '1', 't'),
        }
        form = SettingsConfigForm(initial=initial_data)

    settings_list = SystemSetting.objects.all().order_by('key')
    return render(request, 'settings/index.html', {'form': form, 'settings_list': settings_list})
