"""
Anomaly Detection Engine.
Evaluates incoming hardware metrics, service states, and security events against configurable thresholds.
Coordinates root cause diagnosis, severity calculation, and duplicate incident prevention.
"""

from django.utils import timezone
from django.conf import settings
from typing import Dict, Any, List, Optional
from ..models import Server, Incident, SecurityEvent, SystemSetting, AuditLog
from .severity_engine import SeverityEngine
from .root_cause_engine import RootCauseEngine


class AnomalyDetector:
    """
    Evaluates server telemetry and manages the lifecycle of incidents and security alerts.
    """

    @classmethod
    def get_thresholds(cls) -> Dict[str, float]:
        """
        Retrieves threshold configurations from Database SystemSettings or falls back to settings.py.
        """
        defaults = getattr(settings, 'LINUXGUARD_CONFIG', {})
        return {
            'cpu_warn': float(SystemSetting.get_setting('CPU_WARN', defaults.get('CPU_WARN', 85.0))),
            'cpu_crit': float(SystemSetting.get_setting('CPU_CRIT', defaults.get('CPU_CRIT', 95.0))),
            'ram_warn': float(SystemSetting.get_setting('RAM_WARN', defaults.get('RAM_WARN', 85.0))),
            'ram_crit': float(SystemSetting.get_setting('RAM_CRIT', defaults.get('RAM_CRIT', 95.0))),
            'disk_warn': float(SystemSetting.get_setting('DISK_WARN', defaults.get('DISK_WARN', 80.0))),
            'disk_crit': float(SystemSetting.get_setting('DISK_CRIT', defaults.get('DISK_CRIT', 90.0))),
            'ssh_limit': int(SystemSetting.get_setting('SSH_FAIL_LIMIT', defaults.get('SSH_FAIL_LIMIT', 5))),
        }

    @classmethod
    def process_system_telemetry(
        cls,
        server: Server,
        telemetry: Dict[str, Any],
        top_processes: List[Dict[str, Any]] = None
    ) -> List[Incident]:
        """
        Analyzes CPU, RAM, and Disk metrics. Creates or updates incidents without duplicate spamming.
        """
        thresholds = cls.get_thresholds()
        created_or_updated = []
        top_procs = top_processes or []

        # 1. CPU Anomaly Check & Recovery
        cpu_usage = telemetry.get('cpu', {}).get('cpu_percent', 0.0)
        if cpu_usage >= thresholds['cpu_warn']:
            severity = SeverityEngine.evaluate_metric_severity(
                'CPU', cpu_usage, thresholds['cpu_warn'], thresholds['cpu_crit']
            )
            diagnosis = RootCauseEngine.diagnose_cpu_incident(cpu_usage, top_procs)
            title = f"High CPU Utilization ({cpu_usage}%) on {server.hostname}"
            desc = f"Server CPU usage reached {cpu_usage}%, surpassing the warning threshold ({thresholds['cpu_warn']}%)."

            inc = cls._create_or_update_incident(
                server=server,
                category=Incident.Category.CPU,
                title=title,
                description=desc,
                severity=severity,
                diagnosis=diagnosis
            )
            created_or_updated.append(inc)
        else:
            # Auto-resolve existing CPU incident if normalized
            existing_cpu = Incident.objects.filter(
                server=server,
                category=Incident.Category.CPU,
                status__in=[Incident.Status.OPEN, Incident.Status.INVESTIGATING]
            ).first()
            if existing_cpu:
                existing_cpu.status = Incident.Status.RESOLVED
                existing_cpu.resolved_at = timezone.now()
                existing_cpu.save()
                AuditLog.objects.create(
                    action="INCIDENT_AUTO_RESOLVED",
                    resource=f"Incident #{existing_cpu.id}",
                    description=f"CPU utilization normalized to {cpu_usage}% on {server.hostname}. Incident marked as RESOLVED.",
                    ip_address="127.0.0.1"
                )

        # 2. RAM Anomaly Check & Recovery
        mem_usage = telemetry.get('memory', {}).get('memory_percent', 0.0)
        swap_usage = telemetry.get('memory', {}).get('swap_percent', 0.0)
        if mem_usage >= thresholds['ram_warn']:
            severity = SeverityEngine.evaluate_metric_severity(
                'MEMORY', mem_usage, thresholds['ram_warn'], thresholds['ram_crit']
            )
            diagnosis = RootCauseEngine.diagnose_memory_incident(mem_usage, top_procs, swap_usage)
            title = f"High Memory Utilization ({mem_usage}%) on {server.hostname}"
            desc = f"Server RAM utilization reached {mem_usage}%, surpassing the warning threshold ({thresholds['ram_warn']}%)."

            inc = cls._create_or_update_incident(
                server=server,
                category=Incident.Category.MEMORY,
                title=title,
                description=desc,
                severity=severity,
                diagnosis=diagnosis
            )
            created_or_updated.append(inc)
        else:
            # Auto-resolve existing RAM incident if normalized
            existing_mem = Incident.objects.filter(
                server=server,
                category=Incident.Category.MEMORY,
                status__in=[Incident.Status.OPEN, Incident.Status.INVESTIGATING]
            ).first()
            if existing_mem:
                existing_mem.status = Incident.Status.RESOLVED
                existing_mem.resolved_at = timezone.now()
                existing_mem.save()
                AuditLog.objects.create(
                    action="INCIDENT_AUTO_RESOLVED",
                    resource=f"Incident #{existing_mem.id}",
                    description=f"RAM utilization normalized to {mem_usage}% on {server.hostname}. Incident marked as RESOLVED.",
                    ip_address="127.0.0.1"
                )

        # 3. Disk Anomaly Check & Recovery
        disk_usage = telemetry.get('disk', {}).get('disk_percent', 0.0)
        mountpoint = telemetry.get('disk', {}).get('mountpoint', '/')
        if disk_usage >= thresholds['disk_warn']:
            severity = SeverityEngine.evaluate_metric_severity(
                'DISK', disk_usage, thresholds['disk_warn'], thresholds['disk_crit']
            )
            diagnosis = RootCauseEngine.diagnose_disk_incident(disk_usage, mountpoint)
            title = f"High Disk Utilization ({disk_usage}%) on {server.hostname} [{mountpoint}]"
            desc = f"Disk partition '{mountpoint}' usage reached {disk_usage}%, surpassing threshold ({thresholds['disk_warn']}%)."

            inc = cls._create_or_update_incident(
                server=server,
                category=Incident.Category.DISK,
                title=title,
                description=desc,
                severity=severity,
                diagnosis=diagnosis
            )
            created_or_updated.append(inc)
        else:
            # Auto-resolve existing Disk incident if normalized
            existing_disk = Incident.objects.filter(
                server=server,
                category=Incident.Category.DISK,
                status__in=[Incident.Status.OPEN, Incident.Status.INVESTIGATING]
            ).first()
            if existing_disk:
                existing_disk.status = Incident.Status.RESOLVED
                existing_disk.resolved_at = timezone.now()
                existing_disk.save()
                AuditLog.objects.create(
                    action="INCIDENT_AUTO_RESOLVED",
                    resource=f"Incident #{existing_disk.id}",
                    description=f"Disk utilization normalized to {disk_usage}% on {server.hostname}. Incident marked as RESOLVED.",
                    ip_address="127.0.0.1"
                )

        return created_or_updated

    @classmethod
    def process_service_status(
        cls,
        server: Server,
        service_result: Dict[str, Any]
    ) -> Optional[Incident]:
        """
        Analyzes status of a monitored service. Raises incident if INACTIVE or FAILED.
        """
        service_name = service_result.get('service_name', 'unknown')
        status = service_result.get('status', 'NOT_FOUND')

        if status in ['FAILED', 'INACTIVE']:
            severity = SeverityEngine.evaluate_service_severity(service_name, status)
            diagnosis = RootCauseEngine.diagnose_service_incident(
                service_name=service_name,
                status=status,
                recent_logs=service_result.get('raw_output')
            )
            title = f"Service '{service_name}' is {status} on {server.hostname}"
            desc = f"Critical system service '{service_name}' was detected in {status} state during automated health check."

            inc = cls._create_or_update_incident(
                server=server,
                category=Incident.Category.SERVICE,
                title=title,
                description=desc,
                severity=severity,
                diagnosis=diagnosis,
                custom_filter_key=f"service_{service_name}"
            )
            return inc

        elif status == 'ACTIVE':
            # Check if an existing open incident exists for this service and mark it resolved
            existing = Incident.objects.filter(
                server=server,
                category=Incident.Category.SERVICE,
                title__icontains=f"'{service_name}'",
                status__in=[Incident.Status.OPEN, Incident.Status.INVESTIGATING]
            ).first()
            if existing:
                existing.status = Incident.Status.RESOLVED
                existing.resolved_at = timezone.now()
                existing.save()
                AuditLog.objects.create(
                    action="INCIDENT_AUTO_RESOLVED",
                    resource=f"Incident #{existing.id}",
                    description=f"Service '{service_name}' has recovered to ACTIVE state. Incident resolved automatically.",
                    ip_address="127.0.0.1"
                )

        return None

    @classmethod
    def process_ssh_security_events(
        cls,
        server: Server,
        ssh_report: Dict[str, Any]
    ) -> List[SecurityEvent]:
        """
        Evaluates SSH brute force detection and creates SecurityEvent alerts and Incident.
        """
        created_events = []
        alerts = ssh_report.get('brute_force_alerts', [])

        for alert in alerts:
            ip = alert['ip']
            count = alert['count']
            targeted_users = alert.get('targeted_users', [])

            # Record SecurityEvent
            sec_event = SecurityEvent.objects.create(
                server=server,
                event_type=SecurityEvent.EventType.SSH_BRUTE_FORCE,
                source_ip=ip,
                description=alert['description'],
                severity=SecurityEvent.Severity.HIGH,
                timestamp=timezone.now()
            )
            created_events.append(sec_event)

            # Check/create corresponding Incident
            diagnosis = RootCauseEngine.diagnose_ssh_brute_force(
                source_ip=ip,
                attempt_count=count,
                targeted_users=targeted_users
            )
            cls._create_or_update_incident(
                server=server,
                category=Incident.Category.SECURITY,
                title=alert['title'],
                description=alert['description'],
                severity=Incident.Severity.HIGH,
                diagnosis=diagnosis,
                custom_filter_key=f"ssh_{ip}"
            )

        return created_events

    @classmethod
    def _create_or_update_incident(
        cls,
        server: Server,
        category: str,
        title: str,
        description: str,
        severity: str,
        diagnosis: Dict[str, Any],
        custom_filter_key: Optional[str] = None
    ) -> Incident:
        """
        Prevents duplicate open incidents for the same problem on the same server.
        """
        # Search for active open or investigating incident
        query = Incident.objects.filter(
            server=server,
            category=category,
            status__in=[Incident.Status.OPEN, Incident.Status.INVESTIGATING]
        )

        if custom_filter_key:
            query = query.filter(title__icontains=custom_filter_key.split('_')[-1])

        existing = query.first()

        if existing:
            # Update severity, evidence, and diagnosis if changed
            existing.severity = severity
            existing.probable_cause = diagnosis.get('probable_cause', existing.probable_cause)
            existing.confidence = diagnosis.get('confidence', existing.confidence)
            existing.recommendation = diagnosis.get('recommendation', existing.recommendation)
            existing.evidence = diagnosis.get('evidence', existing.evidence)
            existing.description = description
            existing.save()
            return existing

        # Create new incident
        new_inc = Incident.objects.create(
            server=server,
            title=title,
            description=description,
            category=category,
            severity=severity,
            status=Incident.Status.OPEN,
            probable_cause=diagnosis.get('probable_cause', ''),
            confidence=diagnosis.get('confidence', 0.0),
            recommendation=diagnosis.get('recommendation', ''),
            evidence=diagnosis.get('evidence', ''),
            detected_at=timezone.now()
        )

        AuditLog.objects.create(
            action="INCIDENT_DETECTED",
            resource=f"Incident #{new_inc.id}",
            description=f"[{severity}] Anomaly detected on {server.hostname}: {title}",
            ip_address="127.0.0.1"
        )

        return new_inc
