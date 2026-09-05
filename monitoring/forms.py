"""
Django Forms for LinuxGuard Platform.
Pure server-side HTML forms with CSRF validation.
"""

from django import forms
from .models import Server, Incident, RemediationAction, User, SystemSetting


class ServerForm(forms.ModelForm):
    class Meta:
        model = Server
        fields = ['hostname', 'ip_address', 'operating_system', 'status', 'is_local', 'description']
        widgets = {
            'hostname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., prod-web-01.company.local'}),
            'ip_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 192.168.1.50'}),
            'operating_system': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Ubuntu 22.04 LTS'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'is_local': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Primary web & API reverse proxy'}),
        }


class IncidentFilterForm(forms.Form):
    server = forms.ModelChoiceField(
        queryset=Server.objects.all(),
        required=False,
        empty_label="All Servers",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    severity = forms.ChoiceField(
        choices=[('', 'All Severities')] + list(Incident.Severity.choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + list(Incident.Status.choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    category = forms.ChoiceField(
        choices=[('', 'All Categories')] + list(Incident.Category.choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class ProcessFilterForm(forms.Form):
    SORT_CHOICES = [
        ('cpu', 'Sort by CPU Usage (High to Low)'),
        ('memory', 'Sort by Memory Usage (High to Low)'),
        ('pid', 'Sort by Process ID'),
        ('name', 'Sort by Process Name'),
    ]
    sort_by = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Filter by process name or user...'})
    )


class RemediationTriggerForm(forms.Form):
    """
    Form to trigger or request a safe remediation action.
    """
    ACTION_CHOICES = [
        ('RESTART_SERVICE', 'Safe Service Restart (systemctl restart <service>)'),
        ('CHECK_SERVICE_STATUS', 'Deep Health Check (systemctl status <service>)'),
        ('COLLECT_SERVICE_LOGS', 'Collect Diagnostic Logs (journalctl -u <service> -n 50)'),
        ('CLEAR_TEMP_CACHE', 'Clean System Temp Cache (safe /tmp files)'),
        ('RELOAD_CONFIG', 'Safe Service Reload (systemctl reload <service>)'),
    ]
    SERVICE_CHOICES = [
        ('nginx', 'nginx - Reverse Proxy & Web Server'),
        ('ssh', 'ssh / sshd - OpenSSH Secure Shell Daemon'),
        ('docker', 'docker - Container Runtime Engine'),
        ('mysql', 'mysql / mariadb - SQL Relational Database'),
        ('postgresql', 'postgresql - PostgreSQL Database Server'),
    ]
    action_type = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    service_name = forms.ChoiceField(
        choices=SERVICE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Explain justification for executing or requesting this remediation...'
        }),
        required=True
    )


class SettingsConfigForm(forms.Form):
    cpu_warn = forms.FloatField(
        label="CPU Warning Threshold (%)",
        min_value=1.0, max_value=100.0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'})
    )
    cpu_crit = forms.FloatField(
        label="CPU Critical Threshold (%)",
        min_value=1.0, max_value=100.0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'})
    )
    ram_warn = forms.FloatField(
        label="RAM Warning Threshold (%)",
        min_value=1.0, max_value=100.0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'})
    )
    ram_crit = forms.FloatField(
        label="RAM Critical Threshold (%)",
        min_value=1.0, max_value=100.0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'})
    )
    disk_warn = forms.FloatField(
        label="Disk Space Warning Threshold (%)",
        min_value=1.0, max_value=100.0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'})
    )
    disk_crit = forms.FloatField(
        label="Disk Space Critical Threshold (%)",
        min_value=1.0, max_value=100.0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'})
    )
    ssh_fail_limit = forms.IntegerField(
        label="SSH Failed Logins Alert Limit (Failures)",
        min_value=1, max_value=100,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    ssh_window_minutes = forms.IntegerField(
        label="SSH Detection Time Window (Minutes)",
        min_value=1, max_value=120,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    auto_remediate_safe_services = forms.BooleanField(
        label="Enable Automatic Self-Healing for Safe Stopped Services (e.g. nginx auto-restart)",
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class AuditFilterForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search action, resource or details...'})
    )
    action = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Filter by action name...'})
    )
