"""
Structured logging utilities for MLOps project.
Provides JSON-formatted logging for training, inference, and system metrics.
"""

import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import structlog


class LogType:
    """Log type constants"""
    TRAINING = "training"
    INFERENCE = "inference"
    SYSTEM = "system"
    API = "api"


def setup_structured_logger(
    name: str,
    log_type: str,
    log_dir: str = "./logs",
    level: str = "INFO"
) -> structlog.BoundLogger:
    """
    Setup a structured logger with JSON output.

    Args:
        name: Logger name
        log_type: Type of log (training, inference, system, api)
        log_dir: Directory to store logs
        level: Logging level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Configured structlog logger
    """
    # Create log directory
    log_path = Path(log_dir) / log_type
    log_path.mkdir(parents=True, exist_ok=True)

    # Create log file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_path / f"{name}_{timestamp}.log"

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Setup standard logging
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # File handler for JSON logs
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(getattr(logging, level.upper()))

    # Console handler for human-readable output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Get structlog logger
    struct_logger = structlog.get_logger(name)

    return struct_logger


class TrainingLogger:
    """Specialized logger for training metrics"""

    def __init__(self, experiment_name: str, log_dir: str = "./logs"):
        self.logger = setup_structured_logger(
            name=experiment_name,
            log_type=LogType.TRAINING,
            log_dir=log_dir
        )
        self.start_time = time.time()

    def log_epoch_start(self, epoch: int, total_epochs: int):
        """Log epoch start"""
        self.logger.info(
            "epoch_start",
            epoch=epoch,
            total_epochs=total_epochs,
            timestamp=datetime.now().isoformat()
        )

    def log_step(
        self,
        epoch: int,
        step: int,
        loss: float,
        learning_rate: float,
        **kwargs
    ):
        """Log training step metrics"""
        self.logger.info(
            "training_step",
            epoch=epoch,
            step=step,
            loss=loss,
            learning_rate=learning_rate,
            timestamp=datetime.now().isoformat(),
            **kwargs
        )

    def log_epoch_end(
        self,
        epoch: int,
        avg_loss: float,
        **kwargs
    ):
        """Log epoch end metrics"""
        elapsed = time.time() - self.start_time
        self.logger.info(
            "epoch_end",
            epoch=epoch,
            avg_loss=avg_loss,
            elapsed_seconds=elapsed,
            timestamp=datetime.now().isoformat(),
            **kwargs
        )

    def log_validation(
        self,
        epoch: int,
        val_loss: float,
        **kwargs
    ):
        """Log validation metrics"""
        self.logger.info(
            "validation",
            epoch=epoch,
            val_loss=val_loss,
            timestamp=datetime.now().isoformat(),
            **kwargs
        )

    def log_error(self, error: str, **kwargs):
        """Log error"""
        self.logger.error(
            "training_error",
            error=error,
            timestamp=datetime.now().isoformat(),
            **kwargs
        )


class InferenceLogger:
    """Specialized logger for inference metrics"""

    def __init__(self, service_name: str, log_dir: str = "./logs"):
        self.logger = setup_structured_logger(
            name=service_name,
            log_type=LogType.INFERENCE,
            log_dir=log_dir
        )

    def log_request(
        self,
        request_id: str,
        prompt: str,
        **kwargs
    ):
        """Log inference request"""
        self.logger.info(
            "inference_request",
            request_id=request_id,
            prompt_length=len(prompt),
            timestamp=datetime.now().isoformat(),
            **kwargs
        )

    def log_response(
        self,
        request_id: str,
        latency_ms: float,
        tokens_generated: int,
        **kwargs
    ):
        """Log inference response"""
        self.logger.info(
            "inference_response",
            request_id=request_id,
            latency_ms=latency_ms,
            tokens_generated=tokens_generated,
            tokens_per_second=tokens_generated / (latency_ms / 1000) if latency_ms > 0 else 0,
            timestamp=datetime.now().isoformat(),
            **kwargs
        )

    def log_error(
        self,
        request_id: str,
        error: str,
        **kwargs
    ):
        """Log inference error"""
        self.logger.error(
            "inference_error",
            request_id=request_id,
            error=error,
            timestamp=datetime.now().isoformat(),
            **kwargs
        )


class SystemLogger:
    """Specialized logger for system metrics"""

    def __init__(self, service_name: str, log_dir: str = "./logs"):
        self.logger = setup_structured_logger(
            name=service_name,
            log_type=LogType.SYSTEM,
            log_dir=log_dir
        )

    def log_gpu_metrics(
        self,
        gpu_id: int,
        gpu_memory_used: int,
        gpu_memory_total: int,
        gpu_utilization: float,
        **kwargs
    ):
        """Log GPU metrics"""
        self.logger.info(
            "gpu_metrics",
            gpu_id=gpu_id,
            gpu_memory_used=gpu_memory_used,
            gpu_memory_total=gpu_memory_total,
            gpu_memory_percent=gpu_memory_used / gpu_memory_total * 100 if gpu_memory_total > 0 else 0,
            gpu_utilization=gpu_utilization,
            timestamp=datetime.now().isoformat(),
            **kwargs
        )

    def log_system_metrics(
        self,
        cpu_percent: float,
        memory_percent: float,
        disk_percent: float,
        **kwargs
    ):
        """Log system metrics"""
        self.logger.info(
            "system_metrics",
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            disk_percent=disk_percent,
            timestamp=datetime.now().isoformat(),
            **kwargs
        )

    def log_event(self, event: str, **kwargs):
        """Log system event"""
        self.logger.info(
            event,
            timestamp=datetime.now().isoformat(),
            **kwargs
        )

    def log_error(self, error: str, **kwargs):
        """Log system error"""
        self.logger.error(
            "system_error",
            error=error,
            timestamp=datetime.now().isoformat(),
            **kwargs
        )


class APILogger:
    """Specialized logger for API requests"""

    def __init__(self, service_name: str, log_dir: str = "./logs"):
        self.logger = setup_structured_logger(
            name=service_name,
            log_type=LogType.API,
            log_dir=log_dir
        )

    def log_request(
        self,
        request_id: str,
        method: str,
        path: str,
        **kwargs
    ):
        """Log API request"""
        self.logger.info(
            "api_request",
            request_id=request_id,
            method=method,
            path=path,
            timestamp=datetime.now().isoformat(),
            **kwargs
        )

    def log_response(
        self,
        request_id: str,
        status_code: int,
        duration_ms: float,
        **kwargs
    ):
        """Log API response"""
        self.logger.info(
            "api_response",
            request_id=request_id,
            status_code=status_code,
            duration_ms=duration_ms,
            timestamp=datetime.now().isoformat(),
            **kwargs
        )

    def log_error(
        self,
        request_id: str,
        error: str,
        status_code: int = 500,
        **kwargs
    ):
        """Log API error"""
        self.logger.error(
            "api_error",
            request_id=request_id,
            error=error,
            status_code=status_code,
            timestamp=datetime.now().isoformat(),
            **kwargs
        )
