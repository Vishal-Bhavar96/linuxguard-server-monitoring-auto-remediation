"""
System Monitor Engine.
Uses psutil to collect real Linux / host system hardware telemetry.
Functions:
- get_cpu_usage()
- get_memory_usage()
- get_disk_usage()
- get_load_average()
- get_network_usage()
- get_uptime()
"""

import os
import time
import psutil
from typing import Dict, Any, Tuple


class SystemMonitor:
    """
    Real telemetry collector using psutil.
    """

    @classmethod
    def get_cpu_usage(cls) -> Dict[str, Any]:
        """
        Returns real overall CPU usage percentage and per-core breakdown.
        """
        cpu_percent = psutil.cpu_percent(interval=0.2)
        per_cpu = psutil.cpu_percent(interval=None, percpu=True)
        cpu_count_logical = psutil.cpu_count(logical=True) or 1
        cpu_count_physical = psutil.cpu_count(logical=False) or 1
        cpu_freq = psutil.cpu_freq()
        current_freq = round(cpu_freq.current, 2) if cpu_freq else 0.0

        return {
            'cpu_percent': round(float(cpu_percent), 2),
            'per_cpu': [round(float(c), 2) for c in per_cpu],
            'logical_cores': cpu_count_logical,
            'physical_cores': cpu_count_physical,
            'frequency_mhz': current_freq,
        }

    @classmethod
    def get_memory_usage(cls) -> Dict[str, Any]:
        """
        Returns real RAM and Swap memory utilization.
        """
        vmem = psutil.virtual_memory()
        swap = psutil.swap_memory()

        total_mb = round(vmem.total / (1024 * 1024), 2)
        used_mb = round(vmem.used / (1024 * 1024), 2)
        free_mb = round(vmem.free / (1024 * 1024), 2)
        available_mb = round(vmem.available / (1024 * 1024), 2)

        return {
            'memory_percent': round(float(vmem.percent), 2),
            'total_mb': total_mb,
            'used_mb': used_mb,
            'free_mb': free_mb,
            'available_mb': available_mb,
            'swap_percent': round(float(swap.percent), 2),
            'swap_total_mb': round(swap.total / (1024 * 1024), 2),
            'swap_used_mb': round(swap.used / (1024 * 1024), 2),
        }

    @classmethod
    def get_disk_usage(cls, path: str = '/') -> Dict[str, Any]:
        """
        Returns real disk usage percentage and space details for a path.
        """
        # Determine appropriate path (root '/' or drive root on Windows)
        target_path = path
        if not os.path.exists(target_path):
            target_path = os.path.abspath(os.sep)

        disk = psutil.disk_usage(target_path)
        total_gb = round(disk.total / (1024 ** 3), 2)
        used_gb = round(disk.used / (1024 ** 3), 2)
        free_gb = round(disk.free / (1024 ** 3), 2)

        partitions = []
        for part in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(part.mountpoint)
                partitions.append({
                    'device': part.device,
                    'mountpoint': part.mountpoint,
                    'fstype': part.fstype,
                    'total_gb': round(usage.total / (1024 ** 3), 2),
                    'used_gb': round(usage.used / (1024 ** 3), 2),
                    'free_gb': round(usage.free / (1024 ** 3), 2),
                    'percent': round(float(usage.percent), 2),
                })
            except (PermissionError, OSError):
                continue

        return {
            'disk_percent': round(float(disk.percent), 2),
            'total_gb': total_gb,
            'used_gb': used_gb,
            'free_gb': free_gb,
            'mountpoint': target_path,
            'partitions': partitions,
        }

    @classmethod
    def get_load_average(cls) -> Dict[str, Any]:
        """
        Returns system load averages (1m, 5m, 15m).
        Uses os.getloadavg() on Linux/Unix, with graceful calculation fallback.
        """
        try:
            if hasattr(os, 'getloadavg'):
                load1, load5, load15 = os.getloadavg()
            else:
                # Approximate from CPU utilization if running on Windows
                cpu = psutil.cpu_percent(interval=0.1) / 100.0 * (psutil.cpu_count() or 1)
                load1, load5, load15 = round(cpu, 2), round(cpu * 0.9, 2), round(cpu * 0.8, 2)
        except Exception:
            load1, load5, load15 = 0.0, 0.0, 0.0

        return {
            'load1': round(float(load1), 2),
            'load5': round(float(load5), 2),
            'load15': round(float(load15), 2),
            'formatted': f"{load1:.2f}, {load5:.2f}, {load15:.2f}"
        }

    @classmethod
    def get_network_usage(cls) -> Dict[str, Any]:
        """
        Returns network I/O counters and bandwidth telemetry.
        """
        net_io = psutil.net_io_counters()
        return {
            'bytes_sent': int(net_io.bytes_sent),
            'bytes_recv': int(net_io.bytes_recv),
            'packets_sent': int(net_io.packets_sent),
            'packets_recv': int(net_io.packets_recv),
            'errin': int(net_io.errin),
            'errout': int(net_io.errout),
            'dropin': int(net_io.dropin),
            'dropout': int(net_io.dropout),
        }

    @classmethod
    def get_uptime(cls) -> Dict[str, Any]:
        """
        Returns system boot time and calculated uptime.
        """
        boot_time = psutil.boot_time()
        uptime_seconds = int(time.time() - boot_time)

        days = uptime_seconds // 86400
        hours = (uptime_seconds % 86400) // 3600
        minutes = (uptime_seconds % 3600) // 60
        seconds = uptime_seconds % 60

        formatted = f"{days}d {hours}h {minutes}m {seconds}s" if days > 0 else f"{hours}h {minutes}m {seconds}s"

        return {
            'uptime_seconds': uptime_seconds,
            'boot_timestamp': boot_time,
            'formatted': formatted,
            'days': days,
            'hours': hours,
            'minutes': minutes,
        }

    @classmethod
    def get_host_info(cls) -> Dict[str, Any]:
        """
        Extracts real host system metadata: hostname, IP address, OS release, kernel, uptime.
        Reads /etc/os-release on Linux or standard platform metadata.
        """
        import socket
        import platform

        hostname = socket.gethostname()
        is_linux = platform.system() == 'Linux'
        kernel_version = platform.uname().release or platform.release()

        # Extract real Linux Distribution name if on Linux
        os_name = f"{platform.system()} {platform.release()}"
        distro_details = ""
        if is_linux and os.path.exists('/etc/os-release'):
            try:
                with open('/etc/os-release', 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith('PRETTY_NAME='):
                            os_name = line.strip().split('=', 1)[1].strip('"\'')
                        elif line.startswith('VERSION='):
                            distro_details = line.strip().split('=', 1)[1].strip('"\'')
            except Exception:
                pass
        elif not is_linux:
            os_name = f"{platform.system()} {platform.release()} (Development Host)"

        # Extract primary network IP
        primary_ip = '127.0.0.1'
        try:
            # Connect dummy socket to determine outgoing interface IP without sending data
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            primary_ip = s.getsockname()[0]
            s.close()
        except Exception:
            try:
                primary_ip = socket.gethostbyname(hostname)
            except Exception:
                primary_ip = '127.0.0.1'

        uptime_info = cls.get_uptime()

        return {
            'hostname': hostname,
            'ip_address': primary_ip,
            'operating_system': os_name,
            'distro_details': distro_details,
            'kernel_version': kernel_version,
            'is_linux': is_linux,
            'architecture': platform.machine(),
            'uptime': uptime_info,
            'status': 'ONLINE',
        }

    @classmethod
    def collect_snapshot(cls) -> Dict[str, Any]:
        """
        Collects a full hardware telemetry snapshot.
        """
        return {
            'host': cls.get_host_info(),
            'cpu': cls.get_cpu_usage(),
            'memory': cls.get_memory_usage(),
            'disk': cls.get_disk_usage(),
            'load_average': cls.get_load_average(),
            'network': cls.get_network_usage(),
            'uptime': cls.get_uptime(),
        }


# Convenience functional wrappers
def get_host_info() -> Dict[str, Any]:
    return SystemMonitor.get_host_info()

def get_cpu_usage() -> Dict[str, Any]:
    return SystemMonitor.get_cpu_usage()

def get_memory_usage() -> Dict[str, Any]:
    return SystemMonitor.get_memory_usage()

def get_disk_usage(path: str = '/') -> Dict[str, Any]:
    return SystemMonitor.get_disk_usage(path)

def get_load_average() -> Dict[str, Any]:
    return SystemMonitor.get_load_average()

def get_network_usage() -> Dict[str, Any]:
    return SystemMonitor.get_network_usage()

def get_uptime() -> Dict[str, Any]:
    return SystemMonitor.get_uptime()

