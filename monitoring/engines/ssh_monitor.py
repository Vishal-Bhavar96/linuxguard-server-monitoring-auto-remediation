"""
SSH Security Monitor Engine.
Analyzes Linux authentication logs and systemd journal for failed SSH attempts.
Detects repeated failures from the same IP within a configurable time window.
Creates SecurityEvent alerts without performing disruptive automatic IP blocking.
"""

import os
import re
import shutil
from collections import defaultdict
from typing import List, Dict, Any
from .command_security import CommandSecurity


class SSHMonitor:
    """
    Detects brute-force authentication attacks on SSH daemons.
    """

    AUTH_LOG_PATHS = [
        '/var/log/auth.log',
        '/var/log/secure',
    ]

    # Regex patterns for SSH failures
    # e.g.: "Failed password for root from 192.168.1.100 port 45322 ssh2"
    # e.g.: "Failed password for invalid user admin from 10.0.0.50 port 51234 ssh2"
    FAILED_SSH_PATTERNS = [
        re.compile(r'Failed password for (?:invalid user )?(\S+) from (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', re.IGNORECASE),
        re.compile(r'Invalid user (\S+) from (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', re.IGNORECASE),
        re.compile(r'authentication failure.*rhost=(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', re.IGNORECASE),
        re.compile(r'Failed publickey for (?:invalid user )?(\S+) from (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', re.IGNORECASE),
    ]

    @classmethod
    def get_raw_auth_logs(cls, max_lines: int = 200) -> List[str]:
        """
        Reads recent authentication log lines from available sources.
        """
        lines = []

        # 1. Check auth log files
        for path in cls.AUTH_LOG_PATHS:
            if os.path.exists(path) and os.path.isfile(path):
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        file_lines = f.readlines()
                        lines.extend([l.strip() for l in file_lines[-max_lines:] if l.strip()])
                except (PermissionError, OSError):
                    pass

        # 2. If no files, or journalctl available, query journalctl
        if not lines and shutil.which('journalctl'):
            res = CommandSecurity.run_safe_command(
                ['journalctl', '-u', 'ssh', '-n', str(max_lines), '--no-pager'],
                timeout=10
            )
            if res['success'] and res['stdout']:
                lines.extend([l.strip() for l in res['stdout'].splitlines() if l.strip()])

        return lines

    @classmethod
    def parse_failed_attempts(cls, log_lines: List[str]) -> List[Dict[str, Any]]:
        """
        Extracts structured records of failed authentication attempts from log lines.
        """
        failures = []
        for line in log_lines:
            for pat in cls.FAILED_SSH_PATTERNS:
                match = pat.search(line)
                if match:
                    groups = match.groups()
                    if len(groups) == 2:
                        user, ip = groups[0], groups[1]
                    else:
                        user, ip = 'unknown', groups[0]

                    failures.append({
                        'ip': ip,
                        'user': user,
                        'log_line': line,
                    })
                    break
        return failures

    @classmethod
    def detect_brute_force(
        cls,
        failure_limit: int = 5,
        custom_logs: List[str] = None
    ) -> Dict[str, Any]:
        """
        Groups failed attempts by IP and returns flagged suspicious IPs exceeding failure_limit.
        """
        logs = custom_logs if custom_logs is not None else cls.get_raw_auth_logs()
        failures = cls.parse_failed_attempts(logs)

        ip_counts = defaultdict(int)
        ip_users = defaultdict(set)
        ip_samples = defaultdict(list)

        for f in failures:
            ip = f['ip']
            ip_counts[ip] += 1
            ip_users[ip].add(f['user'])
            if len(ip_samples[ip]) < 3:
                ip_samples[ip].append(f['log_line'])

        alerts = []
        for ip, count in ip_counts.items():
            if count >= failure_limit:
                alerts.append({
                    'ip': ip,
                    'count': count,
                    'targeted_users': list(ip_users[ip]),
                    'sample_logs': ip_samples[ip],
                    'severity': 'HIGH',
                    'title': f"Possible SSH Brute Force Activity from {ip}",
                    'description': f"Detected {count} failed SSH authentication attempts from source IP {ip}. Targeted accounts: {', '.join(list(ip_users[ip]))}.",
                })

        return {
            'total_failed_logins': len(failures),
            'unique_ips': len(ip_counts),
            'brute_force_alerts': alerts,
            'ip_summary': dict(ip_counts),
        }
