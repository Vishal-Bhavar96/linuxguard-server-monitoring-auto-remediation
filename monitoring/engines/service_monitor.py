"""
Service Monitor Engine.
Safely queries systemd service statuses using allowlisted systemctl commands without shell=True.
Monitors: ssh, nginx, docker, mysql, postgresql.
"""

import shutil
from typing import Dict, Any, List
from .command_security import CommandSecurity, ALLOWED_SERVICES, CommandSecurityError


class ServiceMonitor:
    """
    Safely monitors Linux systemd daemons and detects service failures.
    """

    DEFAULT_SERVICES = ['ssh', 'nginx', 'docker', 'mysql', 'postgresql']

    @classmethod
    def check_service_exists(cls, service_name: str) -> bool:
        """
        Verifies whether a systemd unit exists on the server.
        """
        # Alias resolution (e.g. ssh -> sshd, mysql -> mariadb)
        service = CommandSecurity.validate_service_name(service_name)

        if not shutil.which('systemctl'):
            return False

        # Check unit status with systemctl list-unit-files
        cmd = ['systemctl', 'list-unit-files', f'{service}*', '--no-pager']
        res = CommandSecurity.run_safe_command(cmd, timeout=10)
        if res['success'] and service in res['stdout']:
            return True

        # Fallback: check status return code
        check_cmd = ['systemctl', 'status', service]
        check_res = CommandSecurity.run_safe_command(check_cmd, timeout=10)
        # Unit not found produces code 4 or "not-found" / "could not be found"
        if "not found" in check_res['stderr'].lower() or "could not be found" in check_res['stderr'].lower():
            return False
        return check_res['returncode'] != 4

    @classmethod
    def get_service_status(cls, service_name: str) -> Dict[str, Any]:
        """
        Queries the current operational state of a service.
        Returns:
            - status: 'ACTIVE', 'INACTIVE', 'FAILED', 'NOT_FOUND'
            - is_active: bool
            - raw_output: str
        """
        try:
            service = CommandSecurity.validate_service_name(service_name)
        except CommandSecurityError as e:
            return {
                'service_name': service_name,
                'status': 'NOT_FOUND',
                'is_active': False,
                'raw_output': str(e),
                'error': True,
            }

        if not shutil.which('systemctl'):
            # Return NOT_FOUND if systemctl is unavailable (e.g. non-systemd or dev Windows)
            return {
                'service_name': service,
                'status': 'NOT_FOUND',
                'is_active': False,
                'raw_output': 'systemctl not found on this environment',
                'error': False,
            }

        # Query systemctl is-active
        cmd = ['systemctl', 'is-active', service]
        res = CommandSecurity.run_safe_command(cmd, timeout=10)
        output = res['stdout'].lower().strip()

        if output == 'active':
            state = 'ACTIVE'
            is_active = True
        elif output == 'inactive':
            state = 'INACTIVE'
            is_active = False
        elif output == 'failed':
            state = 'FAILED'
            is_active = False
        else:
            if 'not-found' in output or res['returncode'] == 4 or 'could not be found' in res['stderr'].lower():
                state = 'NOT_FOUND'
            elif res['returncode'] == 3:  # inactive or failed
                state = 'INACTIVE'
            else:
                state = 'FAILED'
            is_active = False

        return {
            'service_name': service,
            'status': state,
            'is_active': is_active,
            'raw_output': res['stdout'] or res['stderr'],
            'error': False,
        }

    @classmethod
    def check_all_services(cls, services: List[str] = None) -> List[Dict[str, Any]]:
        """
        Checks status of all monitored daemons.
        """
        target_services = services or cls.DEFAULT_SERVICES
        results = []
        for s in target_services:
            results.append(cls.get_service_status(s))
        return results

    @classmethod
    def get_service_logs(cls, service_name: str, lines: int = 50) -> Dict[str, Any]:
        """
        Fetches recent journalctl logs for a service.
        """
        service = CommandSecurity.validate_service_name(service_name)
        cmd = ['journalctl', '-u', service, '-n', str(lines), '--no-pager']
        return CommandSecurity.run_safe_command(cmd, timeout=15)
