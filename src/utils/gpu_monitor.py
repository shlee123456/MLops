"""
GPU monitoring utility with structured logging.
"""

import time
import psutil
from typing import Optional
from .logging_utils import SystemLogger

try:
    import pynvml
    NVML_AVAILABLE = True
except ImportError:
    NVML_AVAILABLE = False
    print("Warning: pynvml not available. GPU monitoring disabled.")


class GPUMonitor:
    """Monitor GPU and system metrics"""

    def __init__(self, log_dir: str = "./logs", interval: int = 10):
        """
        Initialize GPU monitor.

        Args:
            log_dir: Directory to store logs
            interval: Monitoring interval in seconds
        """
        self.logger = SystemLogger("gpu_monitor", log_dir=log_dir)
        self.interval = interval
        self.running = False

        if NVML_AVAILABLE:
            try:
                pynvml.nvmlInit()
                self.device_count = pynvml.nvmlDeviceGetCount()
                self.logger.log_event(
                    "gpu_monitor_initialized",
                    device_count=self.device_count
                )
            except Exception as e:
                self.logger.log_error(f"Failed to initialize NVML: {e}")
                self.device_count = 0
        else:
            self.device_count = 0

    def get_gpu_metrics(self, gpu_id: int) -> Optional[dict]:
        """Get metrics for a specific GPU"""
        if not NVML_AVAILABLE:
            return None

        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_id)

            # Memory info
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)

            # Utilization
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)

            # Temperature
            temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)

            # Power
            power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # Convert to Watts

            return {
                "gpu_id": gpu_id,
                "gpu_memory_used": mem_info.used,
                "gpu_memory_total": mem_info.total,
                "gpu_memory_free": mem_info.free,
                "gpu_utilization": util.gpu,
                "gpu_memory_utilization": util.memory,
                "temperature": temp,
                "power_watts": power
            }
        except Exception as e:
            self.logger.log_error(f"Failed to get GPU {gpu_id} metrics: {e}")
            return None

    def get_system_metrics(self) -> dict:
        """Get system metrics"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "swap_percent": psutil.swap_memory().percent
        }

    def log_all_metrics(self):
        """Log GPU and system metrics"""
        # Log GPU metrics
        for gpu_id in range(self.device_count):
            metrics = self.get_gpu_metrics(gpu_id)
            if metrics:
                self.logger.log_gpu_metrics(**metrics)

        # Log system metrics
        sys_metrics = self.get_system_metrics()
        self.logger.log_system_metrics(**sys_metrics)

    def start_monitoring(self):
        """Start continuous monitoring"""
        self.running = True
        self.logger.log_event("monitoring_started", interval=self.interval)

        try:
            while self.running:
                self.log_all_metrics()
                time.sleep(self.interval)
        except KeyboardInterrupt:
            self.stop_monitoring()

    def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False
        self.logger.log_event("monitoring_stopped")

        if NVML_AVAILABLE:
            pynvml.nvmlShutdown()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop_monitoring()


if __name__ == "__main__":
    # Example usage
    with GPUMonitor(log_dir="./logs", interval=5) as monitor:
        print("GPU monitoring started. Press Ctrl+C to stop.")
        monitor.start_monitoring()
