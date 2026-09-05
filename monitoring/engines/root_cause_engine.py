"""
Root Cause Engine.
Rule-based diagnostic reasoning engine that identifies probable causes,
confidence scores, supporting evidence, and actionable remediation guidance.
"""

from typing import Dict, Any, List, Optional


class RootCauseEngine:
    """
    Expert rule-based system analyzing system faults and telemetry.
    """

    @classmethod
    def diagnose_cpu_incident(
        cls,
        cpu_usage: float,
        top_processes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Diagnoses high CPU usage by correlating overall CPU with top process consumption.
        """
        if not top_processes:
            return {
                'probable_cause': f"System-wide high CPU load ({cpu_usage}%).",
                'confidence': 70.0,
                'evidence': f"Overall CPU utilization reached {cpu_usage}%, but no single process dominated the process table.",
                'recommendation': "Inspect background cron tasks, I/O wait times, or kernel thread activity.",
            }

        top_proc = top_processes[0]
        top_cpu = top_proc.get('cpu_percent', 0.0)

        if top_cpu >= 70.0:
            return {
                'probable_cause': f"Runaway High CPU Process: '{top_proc['name']}' (PID {top_proc['pid']})",
                'confidence': 92.0,
                'evidence': (
                    f"Process '{top_proc['name']}' (PID {top_proc['pid']}, User: {top_proc.get('username', 'root')}) "
                    f"is consuming {top_cpu}% CPU, accounting for the majority of overall {cpu_usage}% load."
                ),
                'recommendation': (
                    f"1. Review process PID {top_proc['pid']} logs.\n"
                    f"2. Restart or reload worker process '{top_proc['name']}'.\n"
                    f"3. Check for infinite loops or resource lock contention."
                ),
            }
        elif len(top_processes) >= 3 and sum(p.get('cpu_percent', 0.0) for p in top_processes[:3]) >= 70.0:
            proc_summary = ", ".join([f"{p['name']} ({p.get('cpu_percent', 0)}%)" for p in top_processes[:3]])
            return {
                'probable_cause': f"Distributed Process Load Contention across multiple workers: {proc_summary}",
                'confidence': 85.0,
                'evidence': f"Top 3 processes combined consume over 70% CPU during high server load ({cpu_usage}%).",
                'recommendation': "Scale application worker pool or implement rate limiting on upstream requests.",
            }
        else:
            return {
                'probable_cause': f"Elevated multi-core computation load ({cpu_usage}%)",
                'confidence': 75.0,
                'evidence': f"CPU saturation observed at {cpu_usage}% distributed across system tasks.",
                'recommendation': "Monitor system load averages and evaluate server vertical scaling.",
            }

    @classmethod
    def diagnose_memory_incident(
        cls,
        mem_usage: float,
        top_processes: List[Dict[str, Any]],
        swap_usage: float = 0.0
    ) -> Dict[str, Any]:
        """
        Diagnoses high RAM utilization and potential memory leaks.
        """
        if top_processes and top_processes[0].get('memory_percent', 0.0) >= 50.0:
            top_proc = top_processes[0]
            return {
                'probable_cause': f"Excessive Memory Allocation / Leak in process '{top_proc['name']}' (PID {top_proc['pid']})",
                'confidence': 90.0,
                'evidence': (
                    f"Process '{top_proc['name']}' alone occupies {top_proc['memory_percent']}% of physical RAM. "
                    f"Overall RAM usage is {mem_usage}%, Swap utilization is {swap_usage}%."
                ),
                'recommendation': (
                    f"1. Inspect process '{top_proc['name']}' memory profiles.\n"
                    f"2. Execute controlled graceful restart of daemon/service.\n"
                    f"3. Verify garbage collection or heap limits."
                ),
            }
        return {
            'probable_cause': f"High System Memory Footprint ({mem_usage}%)",
            'confidence': 78.0,
            'evidence': f"Total RAM utilization reached {mem_usage}%. Swap usage: {swap_usage}%.",
            'recommendation': "Check database buffer pools, web server worker memory bounds, and cache eviction policies.",
        }

    @classmethod
    def diagnose_disk_incident(
        cls,
        disk_usage: float,
        mountpoint: str = '/',
        alerts: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Diagnoses disk space saturation.
        """
        return {
            'probable_cause': f"Filesystem Capacity Exhaustion on mount '{mountpoint}' ({disk_usage}%)",
            'confidence': 88.0,
            'evidence': (
                f"Mount '{mountpoint}' has reached {disk_usage}% capacity. "
                "Unattended accumulation of log files, temporary dumps, or database growth."
            ),
            'recommendation': (
                f"1. Check large log directories in /var/log/ or /tmp.\n"
                f"2. Run logrotate or vacuum database WAL files.\n"
                f"3. Expand virtual block storage or purge old system backups."
            ),
        }

    @classmethod
    def diagnose_service_incident(
        cls,
        service_name: str,
        status: str,
        recent_logs: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Diagnoses service downtime or unexpected crash.
        """
        evidence_text = f"Service '{service_name}' status reported as '{status}' by systemctl."
        if recent_logs:
            evidence_text += f"\nRecent service logs:\n{recent_logs[:300]}"

        return {
            'probable_cause': f"Daemon Failure / Unexpected Termination of '{service_name}' service",
            'confidence': 92.0,
            'evidence': evidence_text,
            'recommendation': (
                f"1. Check configuration syntax for '{service_name}'.\n"
                f"2. Execute safe service restart (systemctl restart {service_name}).\n"
                f"3. Inspect journalctl -u {service_name} for fatal crash stacks."
            ),
        }

    @classmethod
    def diagnose_ssh_brute_force(
        cls,
        source_ip: str,
        attempt_count: int,
        targeted_users: List[str]
    ) -> Dict[str, Any]:
        """
        Diagnoses repeated SSH authentication failures.
        """
        users_str = ", ".join(targeted_users[:5]) if targeted_users else "root/admin"
        return {
            'probable_cause': f"Automated SSH Dictionary / Brute-Force Attack originating from {source_ip}",
            'confidence': 96.0,
            'evidence': (
                f"Detected {attempt_count} failed SSH password attempts within a short interval from IP {source_ip}. "
                f"Targeted usernames include: {users_str}."
            ),
            'recommendation': (
                f"1. Review source IP {source_ip} origin.\n"
                f"2. Enforce SSH public-key-only authentication (disable PasswordAuthentication).\n"
                f"3. Configure fail2ban jail or hardware firewall rate limiting.\n"
                f"4. Disable direct root SSH login (PermitRootLogin no)."
            ),
        }
