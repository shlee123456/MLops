#!/usr/bin/env python3
"""
Example: Training script with integrated structured logging

This is a simplified example showing how to use the logging utilities.
For full training scripts, see 01_lora_finetune.py and 02_qlora_finetune.py
"""

import os
import sys
import time
import torch
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils.logging_utils import TrainingLogger, SystemLogger
from src.utils.gpu_monitor import GPUMonitor


def example_training():
    """Example training loop with logging"""

    # Initialize loggers
    experiment_name = "example_experiment"
    training_logger = TrainingLogger(experiment_name, log_dir="./logs")
    system_logger = SystemLogger("example_system", log_dir="./logs")

    # Log training start
    system_logger.log_event(
        "training_started",
        model_name="example-model",
        num_epochs=3,
        batch_size=4
    )

    # Simulated training loop
    num_epochs = 3
    steps_per_epoch = 10

    for epoch in range(1, num_epochs + 1):
        # Log epoch start
        training_logger.log_epoch_start(epoch=epoch, total_epochs=num_epochs)

        epoch_losses = []

        for step in range(1, steps_per_epoch + 1):
            # Simulate training step
            time.sleep(0.1)  # Simulate computation
            loss = 1.0 / (epoch * step)  # Fake decreasing loss
            learning_rate = 0.0001

            # Log step metrics
            training_logger.log_step(
                epoch=epoch,
                step=step,
                loss=loss,
                learning_rate=learning_rate
            )

            epoch_losses.append(loss)

            # Log GPU metrics (if available)
            if torch.cuda.is_available():
                gpu_memory_used = torch.cuda.memory_allocated()
                gpu_memory_total = torch.cuda.get_device_properties(0).total_memory
                gpu_utilization = (gpu_memory_used / gpu_memory_total) * 100

                system_logger.log_gpu_metrics(
                    gpu_id=0,
                    gpu_memory_used=gpu_memory_used,
                    gpu_memory_total=gpu_memory_total,
                    gpu_utilization=gpu_utilization
                )

        # Log epoch end
        avg_loss = sum(epoch_losses) / len(epoch_losses)
        training_logger.log_epoch_end(epoch=epoch, avg_loss=avg_loss)

    # Log training completion
    system_logger.log_event(
        "training_completed",
        final_loss=avg_loss,
        total_epochs=num_epochs
    )

    print(f"\n✓ Training complete!")
    print(f"📊 Logs saved to: ./logs/training/")
    print(f"\nView logs in Grafana:")
    print(f"  1. Start services: docker-compose up -d")
    print(f"  2. Open Grafana: http://localhost:3000")
    print(f"  3. Go to Explore > Loki")
    print(f'  4. Query: {{job="training"}}')


def example_gpu_monitoring():
    """Example GPU monitoring"""
    print("\nStarting GPU monitoring (10 seconds)...")

    with GPUMonitor(log_dir="./logs", interval=2) as monitor:
        # Monitor for 10 seconds
        for i in range(5):
            monitor.log_all_metrics()
            time.sleep(2)

    print(f"\n✓ GPU monitoring complete!")
    print(f"📊 Logs saved to: ./logs/system/")


if __name__ == "__main__":
    print("="*60)
    print("  Training with Logging Example")
    print("="*60)

    print("\n1. Running example training loop...")
    example_training()

    print("\n2. Running GPU monitoring example...")
    example_gpu_monitoring()

    print("\n" + "="*60)
    print("  All examples completed!")
    print("="*60)
