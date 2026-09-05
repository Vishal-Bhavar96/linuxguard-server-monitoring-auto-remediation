"""
Unit tests for Log Analyzer and SSH Security Monitor.
"""

from monitoring.engines.log_analyzer import LogAnalyzer
from monitoring.engines.ssh_monitor import SSHMonitor


def test_log_line_severity_parsing():
    # Test error
    err_res = LogAnalyzer.parse_log_line("Mar 10 14:22:01 server systemd[1]: Failed to start Nginx HTTP Server.")
    assert err_res['severity'] == 'ERROR'

    # Test critical
    crit_res = LogAnalyzer.parse_log_line("kernel: [12345.67] Out of memory: Kill process 1234 (python) score 850")
    assert crit_res['severity'] == 'CRITICAL'

    # Test info
    info_res = LogAnalyzer.parse_log_line("Mar 10 14:22:01 server CRON[123]: (root) CMD (run-parts /etc/cron.hourly)")
    assert info_res['severity'] == 'INFO'


def test_ssh_brute_force_detection():
    sample_logs = [
        "Mar 10 12:00:01 host sshd[100]: Failed password for root from 192.168.1.50 port 45123 ssh2",
        "Mar 10 12:00:05 host sshd[101]: Failed password for root from 192.168.1.50 port 45124 ssh2",
        "Mar 10 12:00:10 host sshd[102]: Failed password for invalid user admin from 192.168.1.50 port 45125 ssh2",
        "Mar 10 12:00:15 host sshd[103]: Failed password for root from 192.168.1.50 port 45126 ssh2",
        "Mar 10 12:00:20 host sshd[104]: Failed password for ubuntu from 192.168.1.50 port 45127 ssh2",
        # Benign login attempt
        "Mar 10 12:00:25 host sshd[105]: Failed password for test from 10.0.0.1 port 33123 ssh2",
    ]

    report = SSHMonitor.detect_brute_force(failure_limit=5, custom_logs=sample_logs)

    assert report['total_failed_logins'] == 6
    assert len(report['brute_force_alerts']) == 1
    alert = report['brute_force_alerts'][0]
    assert alert['ip'] == '192.168.1.50'
    assert alert['count'] == 5
    assert 'root' in alert['targeted_users']
    assert 'admin' in alert['targeted_users']
