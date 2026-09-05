"""
Network Monitor Engine.
Extracts network throughput, interfaces, active sockets, and connection states.
"""

import shutil
import psutil
from typing import Dict, Any, List
from .command_security import CommandSecurity


class NetworkMonitor:
    """
    Monitors Linux network interfaces, throughput, and TCP/UDP connections.
    """

    @classmethod
    def get_network_overview(cls) -> Dict[str, Any]:
        """
        Collects comprehensive network telemetry.
        """
        io_counters = psutil.net_io_counters()

        # Interface details
        interfaces = []
        if_addrs = psutil.net_if_addrs()
        if_stats = psutil.net_if_stats()

        for if_name, addrs in if_addrs.items():
            stat = if_stats.get(if_name)
            is_up = stat.isup if stat else False
            speed_mbps = stat.speed if stat else 0

            ip_list = []
            for addr in addrs:
                ip_list.append({
                    'family': str(addr.family),
                    'address': addr.address,
                    'netmask': addr.netmask or '',
                })

            interfaces.append({
                'name': if_name,
                'is_up': is_up,
                'speed_mbps': speed_mbps,
                'addresses': ip_list,
            })

        # Connections summary
        connection_counts = {
            'ESTABLISHED': 0,
            'LISTEN': 0,
            'TIME_WAIT': 0,
            'CLOSE_WAIT': 0,
            'OTHER': 0,
            'TOTAL': 0,
        }

        try:
            conns = psutil.net_connections(kind='inet')
            for conn in conns:
                connection_counts['TOTAL'] += 1
                st = conn.status
                if st in connection_counts:
                    connection_counts[st] += 1
                else:
                    connection_counts['OTHER'] += 1
        except (psutil.AccessDenied, PermissionError):
            # Non-root process might not see all connections
            pass

        # Raw ss / ip output if available
        ss_output = ""
        if shutil.which('ss'):
            res = CommandSecurity.run_safe_command(['ss', '-tuln'], timeout=10)
            if res['success']:
                ss_output = res['stdout']

        return {
            'bytes_sent': io_counters.bytes_sent,
            'bytes_recv': io_counters.bytes_recv,
            'bytes_sent_mb': round(io_counters.bytes_sent / (1024 * 1024), 2),
            'bytes_recv_mb': round(io_counters.bytes_recv / (1024 * 1024), 2),
            'packets_sent': io_counters.packets_sent,
            'packets_recv': io_counters.packets_recv,
            'errin': io_counters.errin,
            'errout': io_counters.errout,
            'dropin': io_counters.dropin,
            'dropout': io_counters.dropout,
            'interfaces': interfaces,
            'connection_counts': connection_counts,
            'ss_output': ss_output,
        }
