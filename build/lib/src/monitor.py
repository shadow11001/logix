import time
import psutil
import platform
import datetime
from typing import Dict, List, Any

class SystemMonitor:
    def __init__(self):
        pass

    def get_system_specs(self) -> Dict[str, Any]:
        """
        Gathers static system specifications.
        """
        try:
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "os": platform.system(),
                "os_release": platform.release(),
                "os_version": platform.version(),
                "cpu_count": psutil.cpu_count(logical=True),
                "cpu_freq_current": f"{psutil.cpu_freq().current:.1f} Mhz" if psutil.cpu_freq() else "Unknown",
                "memory_total_gb": f"{mem.total / (1024**3):.2f}",
                "disk_total_gb": f"{disk.total / (1024**3):.2f}",
                "disk_free_gb": f"{disk.free / (1024**3):.2f}",
                "boot_time": datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            return {"error": f"Failed to gather specs: {str(e)}"}

    def monitor_performance(self, duration: int = 60, interval: int = 5) -> Dict[str, Any]:
        """
        Monitors system performance for a set duration.
        """
        samples = []
        start_time = time.time()
        
        # Initial CPU reading (discard first blocking call or immediate return)
        psutil.cpu_percent(interval=None)

        while (time.time() - start_time) < duration:
            # Sleep first to allow CPU interval measurement
            time.sleep(interval)
            
            try:
                # Capture snapshot
                snapshot = {
                    "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                    "cpu_percent": psutil.cpu_percent(interval=None),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_io": None, # Complex to diff, skipping for simple version
                    "net_io": None   # Complex to diff
                }
                
                # Add Load Avg if on Unix
                if hasattr(os, 'getloadavg'):
                    snapshot['load_avg'] = os.getloadavg()

                samples.append(snapshot)
            except Exception:
                continue
                
        # Calculate summary
        if not samples:
            return {"error": "No data collected"}

        avg_cpu = sum(s['cpu_percent'] for s in samples) / len(samples)
        max_cpu = max(s['cpu_percent'] for s in samples)
        avg_mem = sum(s['memory_percent'] for s in samples) / len(samples)
        
        return {
            "duration": duration,
            "interval": interval,
            "samples": samples,
            "summary": {
                "avg_cpu_usage": f"{avg_cpu:.1f}%",
                "max_cpu_usage": f"{max_cpu:.1f}%",
                "avg_mem_usage": f"{avg_mem:.1f}%",
            }
        }
import os