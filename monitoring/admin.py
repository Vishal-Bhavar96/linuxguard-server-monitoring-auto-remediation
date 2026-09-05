"""
Django admin configuration for LinuxGuard models.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Server, SystemMetric, ProcessMetric, ServiceStatus,
    Incident, RemediationAction, AuditLog, SecurityEvent, SystemSetting
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'department', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('LinuxGuard RBAC Profile', {'fields': ('role', 'department', 'phone_number')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('LinuxGuard RBAC Profile', {'fields': ('role', 'department', 'phone_number')}),
    )


@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    list_display = ('hostname', 'ip_address', 'operating_system', 'status', 'is_local', 'last_seen')
    list_filter = ('status', 'is_local', 'operating_system')
    search_fields = ('hostname', 'ip_address')


@admin.register(SystemMetric)
class SystemMetricAdmin(admin.ModelAdmin):
    list_display = ('server', 'cpu_usage', 'memory_usage', 'disk_usage', 'load_average', 'timestamp')
    list_filter = ('server', 'timestamp')
    date_hierarchy = 'timestamp'


@admin.register(ProcessMetric)
class ProcessMetricAdmin(admin.ModelAdmin):
    list_display = ('server', 'pid', 'process_name', 'cpu_percent', 'memory_percent', 'username', 'status', 'timestamp')
    list_filter = ('server', 'username', 'status')
    search_fields = ('process_name', 'username')


@admin.register(ServiceStatus)
class ServiceStatusAdmin(admin.ModelAdmin):
    list_display = ('server', 'service_name', 'status', 'checked_at')
    list_filter = ('status', 'service_name')


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ('title', 'server', 'category', 'severity', 'status', 'confidence', 'detected_at', 'resolved_at')
    list_filter = ('severity', 'status', 'category', 'server')
    search_fields = ('title', 'description', 'probable_cause')


@admin.register(RemediationAction)
class RemediationActionAdmin(admin.ModelAdmin):
    list_display = ('action_name', 'incident', 'command_type', 'status', 'approved_by', 'executed_at')
    list_filter = ('status', 'command_type')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'resource', 'ip_address')
    list_filter = ('action', 'timestamp')
    search_fields = ('description', 'resource', 'action')
    readonly_fields = ('timestamp', 'user', 'action', 'resource', 'description', 'ip_address')


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'server', 'event_type', 'source_ip', 'severity')
    list_filter = ('event_type', 'severity', 'server')
    search_fields = ('description', 'source_ip')


@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'description', 'updated_at')
    search_fields = ('key', 'description')
