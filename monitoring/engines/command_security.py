"""
Command Security Module.
Enforces strict allowlisting, validates inputs, and executes commands safely using subprocess.run(shell=False).
"""

import subprocess
import time
from typing import List, Dict, Any, Optional

ALLOWED_SERVICES = {
    'ssh',
    'sshd',
    'nginx',
    'docker',
    'mysql',
    'mariadb',
    'postgresql',
}

ALLOWED_COMMAND_TEMPLATES = {
    'systemctl_status': ['systemctl', 'status', '{service}'],
    'systemctl_is_active': ['systemctl', 'is-active', '{service}'],
    'systemctl_restart': ['systemctl', 'restart', '{service}'],
    'systemctl_reload': ['systemctl', 'reload', '{service}'],
    'systemctl_list_units': ['systemctl', 'list-unit-files', '--type=service', '--full', '--no-pager'],
    'journalctl_service': ['journalctl', '-u', '{service}', '-n', '50', '--no-pager'],
    'journalctl_errors': ['journalctl', '-p', 'err..alert', '-n', '50', '--no-pager'],
    'df_report': ['df', '-h'],
    'free_report': ['free', '-m'],
    'uptime_report': ['uptime'],
    'ss_summary': ['ss', '-tuln'],
    'ip_addr': ['ip', '-brief', 'address'],
    'safe_clear_tmp': ['find', '/tmp', '-type', 'f', '-atime', '+7', '-delete'],
}

FORBIDDEN_COMMAND_PATTERNS = [
    'rm',
    'rm -rf',
    'shutdown',
    'reboot',
    'userdel',
    'kill -9',
    'chmod -R',
    'chown -R',
    'mkfs',
    'dd',
    '> /dev/sda',
]


class CommandSecurityError(Exception):
    """Raised when an unsafe or non-allowlisted command execution is attempted."""
    pass


class CommandSecurity:
    """
    Security gatekeeper for Linux command execution.
    """

    @classmethod
    def validate_service_name(cls, service_name: str) -> str:
        """
        Validate that service name is strictly alphanumeric and in the allowlist.
        """
        cleaned = service_name.strip().lower()
        if cleaned not in ALLOWED_SERVICES:
            raise CommandSecurityError(
                f"Service '{service_name}' is not in the allowed services list: {sorted(list(ALLOWED_SERVICES))}"
            )
        return cleaned

    @classmethod
    def check_for_forbidden_patterns(cls, command_str: str) -> None:
        """
        Checks if a command contains forbidden or dangerous patterns.
        """
        lower_cmd = command_str.lower()
        for forbidden in FORBIDDEN_COMMAND_PATTERNS:
            if forbidden in lower_cmd:
                raise CommandSecurityError(
                    f"Command contains forbidden dangerous pattern '{forbidden}'. Execution blocked."
                )

    @classmethod
    def build_safe_command(cls, template_key: str, **kwargs) -> List[str]:
        """
        Builds a safe, tokenized command list from a predefined template.
        """
        if template_key not in ALLOWED_COMMAND_TEMPLATES:
            raise CommandSecurityError(f"Command template '{template_key}' is not recognized.")

        template = ALLOWED_COMMAND_TEMPLATES[template_key]
        command_tokens = []
        for token in template:
            if '{service}' in token:
                service = kwargs.get('service')
                if not service:
                    raise CommandSecurityError("Missing required parameter 'service'.")
                valid_service = cls.validate_service_name(service)
                command_tokens.append(token.format(service=valid_service))
            else:
                command_tokens.append(token)
        return command_tokens

    @classmethod
    def run_safe_command(
        cls,
        command_tokens: List[str],
        timeout: int = 30,
        mock_output: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes a command safely using subprocess.run with shell=False.
        """
        # Validate tokens
        if not command_tokens or not isinstance(command_tokens, list):
            raise CommandSecurityError("Command must be a non-empty list of tokens.")

        # Check for forbidden patterns in joined string
        full_command_str = " ".join(command_tokens)
        cls.check_for_forbidden_patterns(full_command_str)

        if mock_output is not None:
            return mock_output

        start_time = time.time()
        try:
            result = subprocess.run(
                command_tokens,
                shell=False,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            duration = round(time.time() - start_time, 3)
            return {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'stdout': result.stdout.strip(),
                'stderr': result.stderr.strip(),
                'command': full_command_str,
                'duration': duration,
            }
        except FileNotFoundError:
            duration = round(time.time() - start_time, 3)
            return {
                'success': False,
                'returncode': 127,
                'stdout': '',
                'stderr': f"Executable not found on this system: '{command_tokens[0]}'",
                'command': full_command_str,
                'duration': duration,
            }
        except subprocess.TimeoutExpired:
            duration = round(time.time() - start_time, 3)
            return {
                'success': False,
                'returncode': 124,
                'stdout': '',
                'stderr': f"Command timed out after {timeout} seconds.",
                'command': full_command_str,
                'duration': duration,
            }
        except Exception as e:
            duration = round(time.time() - start_time, 3)
            return {
                'success': False,
                'returncode': 1,
                'stdout': '',
                'stderr': f"Execution error: {str(e)}",
                'command': full_command_str,
                'duration': duration,
            }
