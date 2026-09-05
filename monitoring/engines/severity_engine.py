"""
Severity Engine.
Calculates standardized severity levels (LOW, MEDIUM, HIGH, CRITICAL)
based on resource saturation, service criticality, security impact, and incident repetition.
"""

from typing import Dict, Any, Optional

CRITICAL_SERVICES = {'ssh', 'sshd', 'nginx', 'mysql', 'mariadb', 'postgresql', 'docker'}


class SeverityEngine:
    """
    Computes weighted incident severity.
    """

    @classmethod
    def evaluate_metric_severity(
        cls,
        metric_type: str,
        value: float,
        warn_thresh: float,
        crit_thresh: float
    ) -> str:
        """
        Evaluates severity for a numeric metric (CPU, RAM, Disk).
        """
        if value >= crit_thresh:
            return 'CRITICAL'
        elif value >= warn_thresh:
            # If close to critical, high; otherwise medium
            if value >= (warn_thresh + crit_thresh) / 2.0:
                return 'HIGH'
            return 'MEDIUM'
        elif value >= (warn_thresh * 0.85):
            return 'LOW'
        return 'LOW'

    @classmethod
    def evaluate_service_severity(cls, service_name: str, status: str) -> str:
        """
        Evaluates severity for stopped or failed services.
        """
        service_clean = service_name.lower().strip()
        is_core = service_clean in CRITICAL_SERVICES

        if status == 'FAILED':
            return 'CRITICAL' if is_core else 'HIGH'
        elif status == 'INACTIVE':
            return 'HIGH' if is_core else 'MEDIUM'
        elif status == 'NOT_FOUND':
            return 'LOW'
        return 'LOW'

    @classmethod
    def evaluate_security_severity(cls, event_type: str, attempt_count: int = 5) -> str:
        """
        Evaluates severity for security alerts.
        """
        if event_type == 'SSH_BRUTE_FORCE':
            if attempt_count >= 20:
                return 'CRITICAL'
            return 'HIGH'
        elif event_type == 'SUDO_FAILURE':
            return 'HIGH'
        elif event_type == 'UNAUTHORIZED_ACCESS':
            return 'CRITICAL'
        elif event_type == 'AUTH_FAILURE':
            return 'MEDIUM'
        return 'LOW'

    @classmethod
    def calculate_composite_severity(
        cls,
        base_severity: str,
        repetition_count: int = 1,
        is_production: bool = True
    ) -> str:
        """
        Elevates severity if an issue recurs multiple monitoring cycles.
        """
        levels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        try:
            idx = levels.index(base_severity)
        except ValueError:
            idx = 1  # MEDIUM default

        # Elevate by 1 level if recurring 3+ times
        if repetition_count >= 3 and idx < len(levels) - 1:
            idx += 1

        return levels[idx]
