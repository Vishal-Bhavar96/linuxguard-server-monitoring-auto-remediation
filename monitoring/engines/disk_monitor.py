"""
Disk Monitor Engine.
Provides comprehensive filesystem utilization reports and threshold violation checks.
Detects:
- Disk > 80% = WARNING
- Disk > 90% = CRITICAL
"""

import shutil
import psutil
from typing import Dict, Any, List
from .command_security import CommandSecurity


class DiskMonitor:
    """
    Analyzes disk space, filesystem mounts, and directory usage.
    """

    @classmethod
    def get_disk_report(cls, warn_threshold: float = 80.0, crit_threshold: float = 90.0) -> Dict[str, Any]:
        """
        Generates detailed disk usage telemetry for all partitions.
        """
        partitions_data = []
        alerts = []
        max_usage = 0.0

        for part in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(part.mountpoint)
                used_pct = round(float(usage.percent), 2)
                total_gb = round(usage.total / (1024 ** 3), 2)
                used_gb = round(usage.used / (1024 ** 3), 2)
                free_gb = round(usage.free / (1024 ** 3), 2)

                if used_pct > max_usage:
                    max_usage = used_pct

                severity = 'NORMAL'
                if used_pct >= crit_threshold:
                    severity = 'CRITICAL'
                    alerts.append({
                        'mountpoint': part.mountpoint,
                        'percent': used_pct,
                        'severity': 'CRITICAL',
                        'message': f"Filesystem on '{part.mountpoint}' is CRITICALLY full ({used_pct}% utilized). Free: {free_gb} GB"
                    })
                elif used_pct >= warn_threshold:
                    severity = 'WARNING'
                    alerts.append({
                        'mountpoint': part.mountpoint,
                        'percent': used_pct,
                        'severity': 'WARNING',
                        'message': f"Filesystem on '{part.mountpoint}' is in WARNING state ({used_pct}% utilized). Free: {free_gb} GB"
                    })

                partitions_data.append({
                    'device': part.device,
                    'mountpoint': part.mountpoint,
                    'fstype': part.fstype,
                    'total_gb': total_gb,
                    'used_gb': used_gb,
                    'free_gb': free_gb,
                    'percent': used_pct,
                    'status': severity,
                })
            except (PermissionError, OSError):
                continue

        # Run df -h if available on Linux for raw system output
        df_raw = ""
        if shutil.which('df'):
            res = CommandSecurity.run_safe_command(['df', '-h'], timeout=10)
            if res['success']:
                df_raw = res['stdout']

        return {
            'partitions': partitions_data,
            'max_usage_percent': max_usage,
            'alerts': alerts,
            'has_critical': any(a['severity'] == 'CRITICAL' for a in alerts),
            'has_warning': any(a['severity'] == 'WARNING' for a in alerts),
            'df_output': df_raw,
        }

    @classmethod
    def get_large_directories(cls, path: str = '/var/log', limit: int = 5) -> List[Dict[str, Any]]:
        """
        Safely identifies large directory sizes in system paths.
        """
        # du -sh /path/*
        if not shutil.which('du'):
            return []

        res = CommandSecurity.run_safe_command(['du', '-sh', f'{path}'], timeout=15)
        if not res['success']:
            return []

        return [{'path': path, 'raw': res['stdout']}]
