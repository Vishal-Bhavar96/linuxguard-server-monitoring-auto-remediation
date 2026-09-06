"""
Database Models for LinuxGuard Platform.
Implements:
- User (RBAC: ADMIN, OPERATOR, VIEWER)
- Server
- SystemMetric
- ProcessMetric
- ServiceStatus
- Incident
- RemediationAction
- AuditLog
- SecurityEvent
- SystemSetting
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    """
    Custom User model with enterprise Role-Based Access Control (RBAC).
    Roles:
    - ADMIN: Full system access, approve dangerous/critical actions, manage settings & users.
    - OPERATOR: Monitoring access, trigger standard safe remediations, manage incidents.
    - VIEWER: Read-only observation access.
    """
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrator'
        OPERATOR = 'OPERATOR', 'System Operator'
        VIEWER = 'VIEWER', 'Auditor / Viewer'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.OPERATOR,
        help_text="Role determining platform permissions."
    )
    department = models.CharField(max_length=100, blank=True, default='')
    phone_number = models.CharField(max_length=30, blank=True, default='')

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['username']

    def is_admin_role(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    def is_operator_role(self):
        return self.role in [self.Role.ADMIN, self.Role.OPERATOR] or self.is_superuser

    def is_viewer_role(self):
        return True

    def can_remediate(self):
        """Check if user has permission to initiate remediation."""
        return self.is_operator_role()

    def can_approve_remediation(self):
        """Check if user has permission to approve sensitive/critical remediation."""
        return self.is_admin_role()

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class Server(models.Model):
    """
    Monitored Linux host metadata.
    """
    class Status(models.TextChoices):
        ONLINE = 'ONLINE', 'Online'
        OFFLINE = 'OFFLINE', 'Offline'
        DEGRADED = 'DEGRADED', 'Degraded'
        CRITICAL = 'CRITICAL', 'Critical'

    hostname = models.CharField(max_length=255, unique=True)
    ip_address = models.GenericIPAddressField(default='127.0.0.1')
    operating_system = models.CharField(max_length=255, default='Ubuntu 22.04 LTS')
    kernel_version = models.CharField(max_length=255, blank=True, default='')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ONLINE
    )
    is_local = models.BooleanField(
        default=False,
        help_text="True if this server corresponds to the local host machine."
    )
    description = models.CharField(max_length=255, blank=True, default='')
    last_seen = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Server'
        verbose_name_plural = 'Servers'
        ordering = ['hostname']

    def __str__(self):
        return f"{self.hostname} ({self.ip_address})"

    @property
    def is_healthy(self):
        return self.status == self.Status.ONLINE

    @property
    def latest_metric(self):
        return self.system_metrics.order_by('-timestamp').first()


class SystemMetric(models.Model):
    """
    Periodic hardware and network telemetry for a server.
    """
    server = models.ForeignKey(
        Server,
        on_delete=models.CASCADE,
        related_name='system_metrics'
    )
    cpu_usage = models.FloatField(help_text="Overall CPU percentage (0.0 - 100.0)")
    memory_usage = models.FloatField(help_text="RAM usage percentage (0.0 - 100.0)")
    disk_usage = models.FloatField(help_text="Root partition disk usage percentage (0.0 - 100.0)")
    network_sent = models.BigIntegerField(default=0, help_text="Total bytes sent")
    network_received = models.BigIntegerField(default=0, help_text="Total bytes received")
    load_average = models.CharField(
        max_length=100,
        default='0.00, 0.00, 0.00',
        help_text="System load average (1m, 5m, 15m)"
    )
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        verbose_name = 'System Metric'
        verbose_name_plural = 'System Metrics'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.server.hostname} @ {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - CPU: {self.cpu_usage}% RAM: {self.memory_usage}%"


class ProcessMetric(models.Model):
    """
    Snapshot of high-consuming processes running on a monitored server.
    """
    server = models.ForeignKey(
        Server,
        on_delete=models.CASCADE,
        related_name='process_metrics'
    )
    pid = models.IntegerField()
    process_name = models.CharField(max_length=255)
    cpu_percent = models.FloatField(default=0.0)
    memory_percent = models.FloatField(default=0.0)
    username = models.CharField(max_length=100, default='root')
    status = models.CharField(max_length=50, default='running')
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        verbose_name = 'Process Metric'
        verbose_name_plural = 'Process Metrics'
        ordering = ['-timestamp', '-cpu_percent']

    def __str__(self):
        return f"{self.process_name} (PID {self.pid}) - CPU: {self.cpu_percent}% MEM: {self.memory_percent}%"


class ServiceStatus(models.Model):
    """
    Health state of monitored systemd daemons (ssh, nginx, docker, mysql, postgresql).
    """
    class State(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active (Running)'
        INACTIVE = 'INACTIVE', 'Inactive (Stopped)'
        FAILED = 'FAILED', 'Failed'
        NOT_FOUND = 'NOT_FOUND', 'Not Installed / Not Found'

    server = models.ForeignKey(
        Server,
        on_delete=models.CASCADE,
        related_name='service_statuses'
    )
    service_name = models.CharField(max_length=100)
    status = models.CharField(
        max_length=50,
        choices=State.choices,
        default=State.NOT_FOUND
    )
    checked_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Service Status'
        verbose_name_plural = 'Service Statuses'
        unique_together = ('server', 'service_name')
        ordering = ['service_name']

    def __str__(self):
        return f"{self.server.hostname} - {self.service_name}: {self.get_status_display()}"


class Incident(models.Model):
    """
    System anomalies, critical events, and health faults.
    """
    class Category(models.TextChoices):
        CPU = 'CPU', 'CPU Saturation'
        MEMORY = 'MEMORY', 'Memory Exhaustion'
        DISK = 'DISK', 'Disk Space'
        SERVICE = 'SERVICE', 'Service Failure'
        NETWORK = 'NETWORK', 'Network Anomaly'
        SECURITY = 'SECURITY', 'Security Alert'
        SYSTEM = 'SYSTEM', 'System Error'

    class Severity(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        CRITICAL = 'CRITICAL', 'Critical'

    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        INVESTIGATING = 'INVESTIGATING', 'Investigating'
        RESOLVED = 'RESOLVED', 'Resolved'
        DISMISSED = 'DISMISSED', 'Dismissed'

    server = models.ForeignKey(
        Server,
        on_delete=models.CASCADE,
        related_name='incidents'
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(
        max_length=50,
        choices=Category.choices,
        default=Category.SYSTEM
    )
    severity = models.CharField(
        max_length=20,
        choices=Severity.choices,
        default=Severity.MEDIUM
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN
    )
    probable_cause = models.TextField(blank=True, default='')
    confidence = models.FloatField(default=0.0, help_text="Confidence percentage 0 - 100%")
    recommendation = models.TextField(blank=True, default='')
    evidence = models.TextField(blank=True, default='', help_text="Detailed diagnostic facts collected.")
    detected_at = models.DateTimeField(default=timezone.now, db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Incident'
        verbose_name_plural = 'Incidents'
        ordering = ['-detected_at']

    def __str__(self):
        return f"[{self.severity}] {self.title} ({self.get_status_display()})"

    @property
    def is_active(self):
        return self.status in [self.Status.OPEN, self.Status.INVESTIGATING]


class RemediationAction(models.Model):
    """
    Controlled remediation executions linked to incidents.
    """
    class Status(models.TextChoices):
        PENDING_APPROVAL = 'PENDING_APPROVAL', 'Pending Approval'
        APPROVED = 'APPROVED', 'Approved'
        EXECUTING = 'EXECUTING', 'Executing'
        SUCCESS = 'SUCCESS', 'Executed Successfully'
        FAILED = 'FAILED', 'Execution Failed'
        REJECTED = 'REJECTED', 'Rejected'

    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name='remediation_actions'
    )
    action_name = models.CharField(max_length=255)
    command_type = models.CharField(
        max_length=100,
        help_text="Predefined action identifier, e.g. RESTART_SERVICE, FLUSH_LOGS, DIAGNOSE_PROCESS"
    )
    status = models.CharField(
        max_length=50,
        choices=Status.choices,
        default=Status.PENDING_APPROVAL
    )
    approved_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='approved_remediations'
    )
    executed_at = models.DateTimeField(null=True, blank=True)
    result = models.TextField(blank=True, default='', help_text="Standard output / error from safe execution.")

    class Meta:
        verbose_name = 'Remediation Action'
        verbose_name_plural = 'Remediation Actions'
        ordering = ['-executed_at', '-id']

    def __str__(self):
        return f"{self.action_name} - {self.get_status_display()}"


class AuditLog(models.Model):
    """
    Immutable security audit trail of all manual and automated operations.
    """
    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=100)
    resource = models.CharField(max_length=255)
    description = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    ip_address = models.CharField(max_length=100, default='127.0.0.1')

    class Meta:
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-timestamp']

    def __str__(self):
        user_str = self.user.username if self.user else "SYSTEM_AUTOMATION"
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {user_str} - {self.action} on {self.resource}"


class SecurityEvent(models.Model):
    """
    Security incidents and authentication alerts (e.g., SSH brute force).
    """
    class EventType(models.TextChoices):
        SSH_BRUTE_FORCE = 'SSH_BRUTE_FORCE', 'SSH Brute Force Attempt'
        AUTH_FAILURE = 'AUTH_FAILURE', 'Authentication Failure'
        SUDO_FAILURE = 'SUDO_FAILURE', 'Sudo Privilege Abuse'
        SUSPICIOUS_LOG = 'SUSPICIOUS_LOG', 'Suspicious System Log Entry'
        UNAUTHORIZED_ACCESS = 'UNAUTHORIZED_ACCESS', 'Unauthorized Access Attempt'

    class Severity(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        CRITICAL = 'CRITICAL', 'Critical'

    server = models.ForeignKey(
        Server,
        on_delete=models.CASCADE,
        related_name='security_events'
    )
    event_type = models.CharField(
        max_length=100,
        choices=EventType.choices,
        default=EventType.AUTH_FAILURE
    )
    source_ip = models.CharField(max_length=100, blank=True, default='')
    description = models.TextField()
    severity = models.CharField(
        max_length=20,
        choices=Severity.choices,
        default=Severity.HIGH
    )
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        verbose_name = 'Security Event'
        verbose_name_plural = 'Security Events'
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.severity}] {self.get_event_type_display()} from {self.source_ip or 'Local'}"


class SystemSetting(models.Model):
    """
    Platform-wide configurable thresholds and behavior toggles.
    """
    key = models.CharField(max_length=100, unique=True)
    value = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, default='')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'System Setting'
        verbose_name_plural = 'System Settings'
        ordering = ['key']

    def __str__(self):
        return f"{self.key} = {self.value}"

    @classmethod
    def get_setting(cls, key: str, default: str = '') -> str:
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_setting(cls, key: str, value: str, description: str = ''):
        obj, created = cls.objects.update_or_create(
            key=key,
            defaults={'value': str(value), 'description': description}
        )
        return obj
