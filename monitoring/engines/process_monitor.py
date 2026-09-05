"""
Process Monitor Engine.
Enumerates Linux / host processes and extracts top CPU and memory consumers using psutil.
"""

import psutil
from typing import List, Dict, Any, Optional


class ProcessMonitor:
    """
    Monitors process activity, CPU/memory consumption, and execution status.
    """

    @classmethod
    def get_all_processes(cls) -> List[Dict[str, Any]]:
        """
        Gathers list of all active processes with relevant telemetry.
        """
        processes = []
        # Pre-populate cpu_percent on first pass if needed, or query direct
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'username', 'status']):
            try:
                info = proc.info
                # Handle None values safely
                cpu_pct = round(float(info.get('cpu_percent') or 0.0), 2)
                mem_pct = round(float(info.get('memory_percent') or 0.0), 2)
                name = info.get('name') or 'unknown'
                username = info.get('username') or 'system'
                status = info.get('status') or 'running'

                processes.append({
                    'pid': info['pid'],
                    'name': name,
                    'cpu_percent': cpu_pct,
                    'memory_percent': mem_pct,
                    'username': username,
                    'status': status,
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception:
                continue

        return processes

    @classmethod
    def get_top_processes(
        cls,
        limit: int = 10,
        sort_by: str = 'cpu',
        filter_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Returns top processes sorted by CPU or memory usage.
        """
        processes = cls.get_all_processes()

        if filter_name:
            filter_lower = filter_name.strip().lower()
            processes = [
                p for p in processes
                if filter_lower in p['name'].lower() or filter_lower in p['username'].lower()
            ]

        if sort_by == 'memory':
            processes.sort(key=lambda p: p['memory_percent'], reverse=True)
        elif sort_by == 'pid':
            processes.sort(key=lambda p: p['pid'])
        elif sort_by == 'name':
            processes.sort(key=lambda p: p['name'].lower())
        else:  # default 'cpu'
            processes.sort(key=lambda p: p['cpu_percent'], reverse=True)

        return processes[:limit]

    @classmethod
    def find_high_consumption_processes(
        cls,
        cpu_threshold: float = 80.0,
        mem_threshold: float = 80.0
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Finds processes exceeding warning/critical resource thresholds.
        """
        processes = cls.get_all_processes()
        high_cpu = [p for p in processes if p['cpu_percent'] >= cpu_threshold]
        high_mem = [p for p in processes if p['memory_percent'] >= mem_threshold]

        high_cpu.sort(key=lambda p: p['cpu_percent'], reverse=True)
        high_mem.sort(key=lambda p: p['memory_percent'], reverse=True)

        return {
            'high_cpu_processes': high_cpu,
            'high_memory_processes': high_mem,
        }
