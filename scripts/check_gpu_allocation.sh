#!/bin/bash
# GPU 할당 확인 스크립트

set -e

echo "=========================================="
echo "GPU Allocation Check"
echo "=========================================="
echo ""

echo "=== System GPU Status ==="
nvidia-smi --query-gpu=index,name,memory.used,memory.total --format=csv
echo ""

echo "=== Container GPU Allocation ==="
if docker ps --format '{{.Names}}' | grep -q "mlops-vllm"; then
    echo "Container: mlops-vllm"
    docker inspect mlops-vllm | jq '.[0].HostConfig.DeviceRequests'
    echo ""
else
    echo "Container 'mlops-vllm' is not running"
    echo ""
fi

echo "=== vLLM Process GPU Usage ==="
if docker ps --format '{{.Names}}' | grep -q "mlops-vllm"; then
    docker exec mlops-vllm nvidia-smi --query-compute-apps=pid,used_memory --format=csv 2>/dev/null || echo "No GPU processes found"
else
    echo "Container 'mlops-vllm' is not running"
fi

echo ""
echo "=========================================="
echo "Check complete"
echo "=========================================="
