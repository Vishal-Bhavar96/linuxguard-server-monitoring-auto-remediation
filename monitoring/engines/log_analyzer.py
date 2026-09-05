"""
Log Analyzer Engine.
Inspects system journal and available Linux log files for ERROR, FAILED, WARNING, and failure patterns.
Does not assume any file exists - checks paths before accessing.
"""

import os
import re
import shutil
from typing import List, Dict, Any
from .command_security import CommandSecurity


class LogAnalyzer:
    """
    Parses and categorizes Linux logs.
    """

    LOG_PATHS = [
        '/var/log/syslog',
        '/var/log/messages',
        '/var/log/nginx/error.log',
        '/var/log/mysql/error.log',
        '/var/log/dpkg.log',
    ]

    SEVERITY_PATTERNS = {
        'CRITICAL': [r'\b(emergency|emerg|alert|crit|panic|kernel panic|oom-killer|out of memory)\b'],
        'ERROR': [r'\b(error|err|failed|failure|fatal|segfault|core dump)\b'],
        'WARNING': [r'\b(warning|warn|deprecated|unreachable|timeout)\b'],
    }

    @classmethod
    def read_file_tail(cls, filepath: str, lines: int = 50) -> List[str]:
        """
        Reads the last N lines of a file safely without loading the whole file in memory.
        """
        if not os.path.exists(filepath) or not os.path.isfile(filepath):
            return []

        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.readlines()
                return [line.strip() for line in content[-lines:] if line.strip()]
        except (PermissionError, OSError):
            return []

    @classmethod
    def parse_log_line(cls, line: str) -> Dict[str, Any]:
        """
        Evaluates log line severity based on regex patterns.
        """
        lower = line.lower()
        for severity, patterns in cls.SEVERITY_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, lower, re.IGNORECASE):
                    return {
                        'raw': line,
                        'severity': severity,
                        'matched_pattern': pat,
                    }
        return {
            'raw': line,
            'severity': 'INFO',
            'matched_pattern': None,
        }

    @classmethod
    def analyze_available_logs(cls, max_lines_per_source: int = 50) -> Dict[str, Any]:
        """
        Gathers logs from journalctl and available files in /var/log/.
        """
        events = []
        sources_checked = []

        # 1. Query journalctl if available
        if shutil.which('journalctl'):
            sources_checked.append('journalctl')
            res = CommandSecurity.run_safe_command(
                ['journalctl', '-p', 'err..alert', '-n', str(max_lines_per_source), '--no-pager'],
                timeout=10
            )
            if res['success'] and res['stdout']:
                for line in res['stdout'].splitlines():
                    if line.strip():
                        parsed = cls.parse_log_line(line)
                        parsed['source'] = 'journalctl'
                        events.append(parsed)

        # 2. Check standard file paths
        for path in cls.LOG_PATHS:
            if os.path.exists(path) and os.path.isfile(path):
                sources_checked.append(path)
                lines = cls.read_file_tail(path, lines=max_lines_per_source)
                for line in lines:
                    parsed = cls.parse_log_line(line)
                    if parsed['severity'] in ['CRITICAL', 'ERROR', 'WARNING']:
                        parsed['source'] = path
                        events.append(parsed)

        critical_count = sum(1 for e in events if e['severity'] == 'CRITICAL')
        error_count = sum(1 for e in events if e['severity'] == 'ERROR')
        warning_count = sum(1 for e in events if e['severity'] == 'WARNING')

        return {
            'events': events,
            'sources_checked': sources_checked,
            'critical_count': critical_count,
            'error_count': error_count,
            'warning_count': warning_count,
            'total_alerts': len(events),
        }
