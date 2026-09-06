"""
Django Management Command: monitor_server
Runs real server telemetry collection, anomaly detection, root cause diagnosis, and safe auto-remediation.
Usage:
    python manage.py monitor_server [--interval SECONDS] [--once] [--server-id ID]
"""

import time
import socket
from django.core.management.base import BaseCommand
from django.utils import timezone
from monitoring.models import Server, SystemMetric, ProcessMetric, ServiceStatus, Incident, RemediationAction, AuditLog
from monitoring.engines.system_monitor import SystemMonitor
from monitoring.engines.process_monitor import ProcessMonitor
from monitoring.engines.service_monitor import ServiceMonitor
from monitoring.engines.ssh_monitor import SSHMonitor
from monitoring.engines.log_analyzer import LogAnalyzer
from monitoring.engines.anomaly_detector import AnomalyDetector
from monitoring.engines.remediation_engine import RemediationEngine


class Command(BaseCommand):
    help = "Monitors Linux/Host server metrics, detects anomalies, creates incidents, and runs safe self-healing."

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=30,
            help="Polling interval in seconds (default: 30s)."
        )
        parser.add_argument(
            '--once',
            action='store_true',
            help="Run a single monitoring cycle and exit."
        )
        parser.add_argument(
            '--server-id',
            type=int,
            default=None,
            help="Specify a particular server ID to monitor. Defaults to monitoring all registered servers or local server."
        )

    def get_or_create_local_server(self) -> Server:
        """
        Ensures the local host server is registered in the database with detected host telemetry.
        """
        host_info = SystemMonitor.get_host_info()
        server, created = Server.objects.get_or_create(
            is_local=True,
            defaults={
                'hostname': host_info['hostname'],
                'ip_address': host_info['ip_address'],
                'operating_system': host_info['operating_system'],
                'kernel_version': host_info.get('kernel_version', ''),
                'status': Server.Status.ONLINE,
                'description': 'Primary Local Host Machine'
            }
        )
        if not created:
            server.operating_system = host_info['operating_system']
            server.kernel_version = host_info.get('kernel_version', '')
            server.ip_address = host_info['ip_address']
            server.save()
        else:
            self.stdout.write(self.style.SUCCESS(f"Registered local host server '{server.hostname}' (IP: {server.ip_address}, OS: {server.operating_system})."))
        return server

    def execute_monitoring_cycle(self, server: Server):
        """
        Single complete telemetry & self-healing execution cycle for a server.
        """
        self.stdout.write(f"[{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}] Monitoring server: {server.hostname} ({server.ip_address})...")

        # 1. Collect real hardware snapshot
        telemetry = SystemMonitor.collect_snapshot()

        # 2. Collect top consuming processes
        top_procs = ProcessMonitor.get_top_processes(limit=10, sort_by='cpu')

        # 3. Store SystemMetric in SQL DB
        metric = SystemMetric.objects.create(
            server=server,
            cpu_usage=telemetry['cpu']['cpu_percent'],
            memory_usage=telemetry['memory']['memory_percent'],
            disk_usage=telemetry['disk']['disk_percent'],
            network_sent=telemetry['network']['bytes_sent'],
            network_received=telemetry['network']['bytes_recv'],
            load_average=telemetry['load_average']['formatted'],
            timestamp=timezone.now()
        )

        # 4. Store ProcessMetric records (top 5 CPU)
        for proc in top_procs[:5]:
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

        # 5. Check and update systemd services
        service_results = ServiceMonitor.check_all_services()
        for s_res in service_results:
            ServiceStatus.objects.update_or_create(
                server=server,
                service_name=s_res['service_name'],
                defaults={
                    'status': s_res['status'],
                    'checked_at': timezone.now()
                }
            )

        # 6. Check SSH Security & Authentication logs
        ssh_report = SSHMonitor.detect_brute_force(failure_limit=5)
        sec_events = AnomalyDetector.process_ssh_security_events(server, ssh_report)
        if sec_events:
            self.stdout.write(self.style.WARNING(f"  [!] Detected {len(sec_events)} SSH security event(s)!"))

        # 7. Run Anomaly Detection on telemetry
        incidents = AnomalyDetector.process_system_telemetry(server, telemetry, top_procs)

        # 8. Run Anomaly Detection on service statuses
        for s_res in service_results:
            serv_inc = AnomalyDetector.process_service_status(server, s_res)
            if serv_inc:
                incidents.append(serv_inc)

                # 9. Auto-remediation workflow for safe services
                if s_res['service_name'] in RemediationEngine.SAFE_AUTO_RESTART_SERVICES and s_res['status'] in ['INACTIVE', 'FAILED']:
                    self.stdout.write(self.style.NOTICE(f"  --> Triggering Safe Auto-Remediation for service '{s_res['service_name']}'..."))
                    rem_action = RemediationEngine.create_remediation_action(
                        incident=serv_inc,
                        action_name=f"Automated Recovery Restart: {s_res['service_name']}",
                        command_type='RESTART_SERVICE',
                        requires_approval=False,
                        user=None
                    )
                    rem_result = RemediationEngine.execute_service_restart(
                        remediation_action=rem_action,
                        service_name=s_res['service_name']
                    )
                    self.stdout.write(f"  --> Remediation Result: {rem_result['status']}")

        # Update server status and last_seen
        active_incidents = Incident.objects.filter(
            server=server,
            status__in=[Incident.Status.OPEN, Incident.Status.INVESTIGATING]
        )
        if active_incidents.filter(severity=Incident.Severity.CRITICAL).exists():
            server.status = Server.Status.CRITICAL
        elif active_incidents.exists():
            server.status = Server.Status.DEGRADED
        else:
            server.status = Server.Status.ONLINE

        server.last_seen = timezone.now()
        server.save()

        self.stdout.write(self.style.SUCCESS(
            f"  [OK] CPU: {telemetry['cpu']['cpu_percent']}% | RAM: {telemetry['memory']['memory_percent']}% | "
            f"Disk: {telemetry['disk']['disk_percent']}% | Active Incidents: {active_incidents.count()}"
        ))

    def handle(self, *args, **options):
        interval = options['interval']
        run_once = options['once']
        server_id = options['server_id']

        self.stdout.write(self.style.SUCCESS("=== LinuxGuard Monitoring Service Started ==="))

        while True:
            if server_id:
                servers = Server.objects.filter(id=server_id)
                if not servers.exists():
                    self.stdout.write(self.style.ERROR(f"Server with ID {server_id} not found."))
                    return
            else:
                servers = Server.objects.all()
                if not servers.exists():
                    self.get_or_create_local_server()
                    servers = Server.objects.all()

            for server in servers:
                try:
                    self.execute_monitoring_cycle(server)
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error monitoring server {server.hostname}: {str(e)}"))

            if run_once:
                self.stdout.write(self.style.SUCCESS("Single monitoring cycle finished."))
                break

            self.stdout.write(f"Sleeping for {interval} seconds...\n")
            time.sleep(interval)
