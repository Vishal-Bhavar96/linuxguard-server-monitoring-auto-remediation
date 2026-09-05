"""
Django Management Command: seed_demo_data
Populates LinuxGuard with default RBAC users, servers, historical metrics, incidents, and audit logs.
"""

from datetime import timedelta
import socket
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from monitoring.models import (
    Server, SystemMetric, ProcessMetric, ServiceStatus,
    Incident, RemediationAction, AuditLog, SecurityEvent, SystemSetting
)

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds database with default users (Admin, Operator, Viewer), servers, metrics, and incidents."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding LinuxGuard demo environment..."))

        # 1. Create Default RBAC Users
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@linuxguard.internal',
                'role': User.Role.ADMIN,
                'is_staff': True,
                'is_superuser': True,
                'department': 'DevOps & Infrastructure'
            }
        )
        admin_user.set_password('AdminPass123!')
        admin_user.save()

        operator_user, _ = User.objects.get_or_create(
            username='operator',
            defaults={
                'email': 'operator@linuxguard.internal',
                'role': User.Role.OPERATOR,
                'is_staff': False,
                'department': 'Site Reliability Engineering'
            }
        )
        operator_user.set_password('OperatorPass123!')
        operator_user.save()

        viewer_user, _ = User.objects.get_or_create(
            username='viewer',
            defaults={
                'email': 'viewer@linuxguard.internal',
                'role': User.Role.VIEWER,
                'is_staff': False,
                'department': 'Security & Compliance'
            }
        )
        viewer_user.set_password('ViewerPass123!')
        viewer_user.save()

        self.stdout.write(self.style.SUCCESS("Created RBAC users: admin, operator, viewer (password: <Role>Pass123!)."))

        # 2. Register Default System Settings
        settings_defaults = [
            ('CPU_WARN', '85.0', 'CPU Warning Threshold (%)'),
            ('CPU_CRIT', '95.0', 'CPU Critical Threshold (%)'),
            ('RAM_WARN', '85.0', 'RAM Warning Threshold (%)'),
            ('RAM_CRIT', '95.0', 'RAM Critical Threshold (%)'),
            ('DISK_WARN', '80.0', 'Disk Warning Threshold (%)'),
            ('DISK_CRIT', '90.0', 'Disk Critical Threshold (%)'),
            ('SSH_FAIL_LIMIT', '5', 'SSH Brute-Force Alert Threshold'),
            ('SSH_WINDOW_MINUTES', '10', 'SSH Detection Window (Minutes)'),
            ('AUTO_REMEDIATE_SAFE_SERVICES', 'True', 'Auto-restart safe stopped daemons'),
        ]
        for key, val, desc in settings_defaults:
            SystemSetting.set_setting(key, val, desc)

        # 3. Create Monitored Servers
        local_hostname = socket.gethostname()
        s_local, _ = Server.objects.get_or_create(
            hostname=local_hostname,
            defaults={
                'ip_address': '127.0.0.1',
                'operating_system': 'Ubuntu Linux 22.04 LTS',
                'status': Server.Status.ONLINE,
                'is_local': True,
                'description': 'Primary Host Machine (Local Node)'
            }
        )

        s_prod, _ = Server.objects.get_or_create(
            hostname='ubuntu-prod-web-01',
            defaults={
                'ip_address': '10.0.1.15',
                'operating_system': 'Ubuntu 22.04 LTS (Jammy Jellyfish)',
                'status': Server.Status.DEGRADED,
                'is_local': False,
                'description': 'Production Web Cluster Reverse Proxy (Nginx/Gunicorn)'
            }
        )

        s_db, _ = Server.objects.get_or_create(
            hostname='ubuntu-db-primary-02',
            defaults={
                'ip_address': '10.0.2.40',
                'operating_system': 'Ubuntu 20.04 LTS',
                'status': Server.Status.ONLINE,
                'is_local': False,
                'description': 'PostgreSQL & Redis Relational Database Cluster'
            }
        )

        s_edge, _ = Server.objects.get_or_create(
            hostname='ubuntu-edge-worker-03',
            defaults={
                'ip_address': '10.0.3.88',
                'operating_system': 'Ubuntu 22.04 LTS',
                'status': Server.Status.CRITICAL,
                'is_local': False,
                'description': 'Background Celery Task Worker & ETL Processing'
            }
        )

        # 4. Generate Telemetry Metrics (Historical Data Points)
        now = timezone.now()
        for idx in range(12):
            ts = now - timedelta(minutes=(12 - idx) * 5)
            # Web server metrics (elevated CPU)
            SystemMetric.objects.create(
                server=s_prod,
                cpu_usage=68.0 + (idx * 2.1) if idx < 8 else 88.5,
                memory_usage=72.0 + (idx * 0.8),
                disk_usage=74.2,
                network_sent=1024 * 1024 * (50 + idx * 8),
                network_received=1024 * 1024 * (120 + idx * 15),
                load_average=f"{1.45 + idx * 0.2:.2f}, 1.20, 0.95",
                timestamp=ts
            )
            # Edge worker metrics (critical CPU)
            SystemMetric.objects.create(
                server=s_edge,
                cpu_usage=96.4,
                memory_usage=89.2,
                disk_usage=91.5,
                network_sent=1024 * 1024 * 35,
                network_received=1024 * 1024 * 80,
                load_average="8.42, 7.15, 6.02",
                timestamp=ts
            )
            # Local server metric
            SystemMetric.objects.create(
                server=s_local,
                cpu_usage=34.2,
                memory_usage=55.0,
                disk_usage=48.0,
                network_sent=1024 * 1024 * 12,
                network_received=1024 * 1024 * 45,
                load_average="0.35, 0.40, 0.42",
                timestamp=ts
            )

        # 5. Add Monitored Services
        services_map = [
            (s_local, 'nginx', ServiceStatus.State.ACTIVE),
            (s_local, 'ssh', ServiceStatus.State.ACTIVE),
            (s_prod, 'nginx', ServiceStatus.State.INACTIVE),
            (s_prod, 'ssh', ServiceStatus.State.ACTIVE),
            (s_prod, 'docker', ServiceStatus.State.ACTIVE),
            (s_db, 'postgresql', ServiceStatus.State.ACTIVE),
            (s_db, 'ssh', ServiceStatus.State.ACTIVE),
            (s_edge, 'docker', ServiceStatus.State.FAILED),
            (s_edge, 'ssh', ServiceStatus.State.ACTIVE),
        ]
        for srv, s_name, state in services_map:
            ServiceStatus.objects.update_or_create(
                server=srv,
                service_name=s_name,
                defaults={'status': state, 'checked_at': now}
            )

        # 6. Add Realistic Incidents with Root Cause Evidence
        inc1, _ = Incident.objects.get_or_create(
            server=s_prod,
            title="Service 'nginx' is INACTIVE on ubuntu-prod-web-01",
            defaults={
                'category': Incident.Category.SERVICE,
                'severity': Incident.Severity.HIGH,
                'status': Incident.Status.OPEN,
                'description': "Nginx reverse proxy stopped responding during health check interval.",
                'probable_cause': "Daemon Failure / Unexpected Termination of 'nginx' service",
                'confidence': 92.0,
                'evidence': "Service 'nginx' status reported as 'INACTIVE' by systemctl. Port 80/443 closed.",
                'recommendation': "Execute safe service restart (systemctl restart nginx) and verify upstream sockets.",
                'detected_at': now - timedelta(minutes=25)
            }
        )

        inc2, _ = Incident.objects.get_or_create(
            server=s_edge,
            title="High CPU Utilization (96.4%) on ubuntu-edge-worker-03",
            defaults={
                'category': Incident.Category.CPU,
                'severity': Incident.Severity.CRITICAL,
                'status': Incident.Status.INVESTIGATING,
                'description': "CPU consumption reached 96.4%, surpassing critical threshold (95.0%).",
                'probable_cause': "Runaway High CPU Process: 'ffmpeg_transcode' (PID 18492)",
                'confidence': 94.0,
                'evidence': "Process 'ffmpeg_transcode' (PID 18492, User: celery) consuming 88.2% CPU across all 4 logical cores.",
                'recommendation': "1. Review PID 18492 logs.\n2. Terminate rogue worker task.\n3. Adjust Celery concurrency limits.",
                'detected_at': now - timedelta(minutes=40)
            }
        )

        inc3, _ = Incident.objects.get_or_create(
            server=s_edge,
            title="High Disk Utilization (91.5%) on ubuntu-edge-worker-03 [/var]",
            defaults={
                'category': Incident.Category.DISK,
                'severity': Incident.Severity.CRITICAL,
                'status': Incident.Status.OPEN,
                'description': "Mount '/var' reached 91.5% utilization, surpassing critical 90% threshold.",
                'probable_cause': "Filesystem Capacity Exhaustion on mount '/var' (91.5%)",
                'confidence': 88.0,
                'evidence': "Mount '/var' is 91.5% utilized. Unattended accumulation of container logs in /var/lib/docker/containers/.",
                'recommendation': "1. Safe clean Docker build cache and logs.\n2. Purge stale /var/tmp files.\n3. Expand volume size.",
                'detected_at': now - timedelta(minutes=15)
            }
        )

        # 7. Remediation Actions
        RemediationAction.objects.get_or_create(
            incident=inc1,
            action_name="Safe Service Restart: nginx",
            defaults={
                'command_type': 'RESTART_SERVICE',
                'status': RemediationAction.Status.PENDING_APPROVAL,
                'approved_by': None,
                'result': ''
            }
        )

        RemediationAction.objects.get_or_create(
            incident=inc3,
            action_name="Safe Clean System Temp Cache",
            defaults={
                'command_type': 'CLEAR_TEMP_CACHE',
                'status': RemediationAction.Status.PENDING_APPROVAL,
                'approved_by': None,
                'result': ''
            }
        )

        # 8. Security Events (SSH Brute Force)
        SecurityEvent.objects.get_or_create(
            server=s_prod,
            event_type=SecurityEvent.EventType.SSH_BRUTE_FORCE,
            source_ip="198.51.100.74",
            defaults={
                'severity': SecurityEvent.Severity.HIGH,
                'description': "Detected 14 failed SSH authentication attempts from source IP 198.51.100.74. Targeted accounts: root, admin, ubuntu.",
                'timestamp': now - timedelta(minutes=30)
            }
        )

        SecurityEvent.objects.get_or_create(
            server=s_edge,
            event_type=SecurityEvent.EventType.AUTH_FAILURE,
            source_ip="203.0.113.42",
            defaults={
                'severity': SecurityEvent.Severity.MEDIUM,
                'description': "Failed SSH password authentication for invalid user 'guest' from 203.0.113.42.",
                'timestamp': now - timedelta(minutes=55)
            }
        )

        # 9. Audit Logs
        AuditLog.objects.create(
            user=admin_user,
            action="SYSTEM_INITIALIZED",
            resource="LinuxGuard Platform",
            description="Initialized platform configuration, seeded RBAC user profiles and monitored nodes.",
            ip_address="127.0.0.1"
        )
        AuditLog.objects.create(
            user=operator_user,
            action="SERVICE_STATUS_CHECK",
            resource="Server: ubuntu-prod-web-01",
            description="Operator performed scheduled manual service status interrogation.",
            ip_address="10.0.1.5"
        )

        self.stdout.write(self.style.SUCCESS("Successfully seeded demo servers, metrics, incidents, security alerts, and audit logs!"))
