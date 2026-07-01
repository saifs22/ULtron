"""
System Monitor — Ultron's eyes on the machine.
Reads CPU, RAM, disk, network, processes, and windows.
"""
import psutil
import platform
from datetime import datetime, timedelta
from typing import Optional


class SystemMonitor:
    """Passive system observation — all read-only, no side effects."""

    RISK_LEVELS = {"*": "low"}

    def get_risk_level(self, tool_input: dict) -> str:
        return "low"

    def describe_action(self, tool_input: dict) -> str:
        action = tool_input.get("action", "full_report")
        return f"Read system metrics ({action})"

    def execute(self, tool_input: dict) -> str:
        """Route to specific monitoring function and return formatted string."""
        action = tool_input.get("action", "full_report")
        handler = getattr(self, f"_get_{action}", None)
        if handler is None:
            return f"Unknown monitor action: {action}"
        result = handler()
        if isinstance(result, dict):
            return self._format_dict(result)
        return str(result)

    # ─── Full Report ─────────────────────────────────────────────────────

    def _get_full_report(self) -> dict:
        """Complete system status report."""
        return {
            "cpu_percent": f"{psutil.cpu_percent(interval=1)}%",
            "cpu_cores": psutil.cpu_count(),
            "ram": self._get_ram(),
            "disk": self._get_disk(),
            "network": self._get_network(),
            "uptime": self._get_uptime(),
            "platform": f"{platform.system()} {platform.release()}",
            "top_processes": self._get_top_processes(),
            "open_windows": self._get_open_windows(),
        }

    # ─── Individual Metrics ──────────────────────────────────────────────

    def _get_cpu(self) -> dict:
        return {
            "percent": psutil.cpu_percent(interval=1),
            "cores_logical": psutil.cpu_count(),
            "cores_physical": psutil.cpu_count(logical=False),
            "freq_mhz": getattr(psutil.cpu_freq(), 'current', 'N/A') if psutil.cpu_freq() else "N/A",
        }

    def _get_ram(self) -> dict:
        mem = psutil.virtual_memory()
        return {
            "total_gb": round(mem.total / (1024**3), 1),
            "used_gb": round(mem.used / (1024**3), 1),
            "available_gb": round(mem.available / (1024**3), 1),
            "percent": mem.percent,
        }

    def _get_disk(self) -> dict:
        partitions = {}
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                partitions[part.mountpoint] = {
                    "total_gb": round(usage.total / (1024**3), 1),
                    "used_gb": round(usage.used / (1024**3), 1),
                    "free_gb": round(usage.free / (1024**3), 1),
                    "percent": usage.percent,
                }
            except PermissionError:
                continue
        return partitions

    def _get_network(self) -> dict:
        counters = psutil.net_io_counters()
        return {
            "bytes_sent_mb": round(counters.bytes_sent / (1024**2), 1),
            "bytes_recv_mb": round(counters.bytes_recv / (1024**2), 1),
            "packets_sent": counters.packets_sent,
            "packets_recv": counters.packets_recv,
        }

    def _get_uptime(self) -> str:
        boot = datetime.fromtimestamp(psutil.boot_time())
        delta = datetime.now() - boot
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes = remainder // 60
        parts = []
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        parts.append(f"{minutes}m")
        return " ".join(parts)

    def _get_top_processes(self, n: int = 5) -> list[dict]:
        """Top N processes by memory usage."""
        procs = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']):
            try:
                info = proc.info
                if info['memory_percent'] and info['memory_percent'] > 0.1:
                    procs.append({
                        "name": info['name'],
                        "pid": info['pid'],
                        "mem_pct": round(info['memory_percent'], 1),
                        "cpu_pct": round(info.get('cpu_percent', 0) or 0, 1),
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        procs.sort(key=lambda x: x['mem_pct'], reverse=True)
        return procs[:n]

    def _get_open_windows(self) -> list[str]:
        """List currently open window titles."""
        try:
            import pygetwindow as gw
            return [w.title for w in gw.getAllWindows() if w.title.strip()]
        except ImportError:
            return ["(pygetwindow not installed)"]
        except Exception:
            return ["(unable to read windows)"]

    def _get_battery(self) -> Optional[dict]:
        """Battery info if available."""
        bat = psutil.sensors_battery()
        if bat is None:
            return None
        return {
            "percent": bat.percent,
            "plugged_in": bat.power_plugged,
            "time_left_min": round(bat.secsleft / 60) if bat.secsleft > 0 else "N/A",
        }

    # ─── Snapshot for Proactive Monitoring ───────────────────────────────

    def get_metrics_snapshot(self) -> dict:
        """Quick lightweight snapshot for background monitoring."""
        return {
            "cpu": psutil.cpu_percent(interval=0),
            "ram": psutil.virtual_memory().percent,
            "disk": psutil.disk_usage('/').percent if platform.system() != "Windows"
                    else psutil.disk_usage('C:\\').percent,
        }

    # ─── Helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _format_dict(d: dict, indent: int = 0) -> str:
        """Format a dict into a readable string."""
        lines = []
        prefix = "  " * indent
        for k, v in d.items():
            if isinstance(v, dict):
                lines.append(f"{prefix}{k}:")
                lines.append(SystemMonitor._format_dict(v, indent + 1))
            elif isinstance(v, list):
                lines.append(f"{prefix}{k}:")
                for item in v:
                    if isinstance(item, dict):
                        lines.append(SystemMonitor._format_dict(item, indent + 1))
                    else:
                        lines.append(f"{prefix}  - {item}")
            else:
                lines.append(f"{prefix}{k}: {v}")
        return "\n".join(lines)
