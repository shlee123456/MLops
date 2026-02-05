#!/bin/bash
# vLLM Multi-Model Startup Script
# 환경변수 기반으로 여러 모델을 각 GPU에서 실행
# Updated: CUDA 12.8 + Blackwell (sm_120) 호환

set -e

# 로그 파일 경로 설정
LOG_DIR="/logs"
mkdir -p "$LOG_DIR"

echo "=========================================="
echo "vLLM Multi-Model Server Starting..."
echo "Logs will be written to: $LOG_DIR"
echo "CUDA Version: $(nvcc --version 2>/dev/null | grep release | awk '{print $5}' | tr -d ',')"
echo "PyTorch Version: $(python -c 'import torch; print(torch.__version__)' 2>/dev/null || echo 'unknown')"
echo "vLLM Version: $(python -c 'import vllm; print(vllm.__version__)' 2>/dev/null || echo 'unknown')"
echo "=========================================="

PIDS=()

# 모델 1 시작
if [ "${MODEL_1_ENABLED:-false}" = "true" ] && [ -n "$MODEL_1_PATH" ]; then
    echo ""
    echo "[Model 1] Starting on GPU ${MODEL_1_GPU:-0}..."
    echo "  Path: $MODEL_1_PATH"
    echo "  Port: ${MODEL_1_PORT:-8000}"
    echo "  GPU Memory: ${MODEL_1_GPU_MEMORY:-0.9}"
    echo "  Max Length: ${MODEL_1_MAX_LEN:-4096}"

    MODEL_1_LOG="$LOG_DIR/model1.log"
    echo "  Log File: $MODEL_1_LOG"

    (CUDA_VISIBLE_DEVICES=${MODEL_1_GPU:-0} vllm serve "$MODEL_1_PATH" \
        --host 0.0.0.0 \
        --port ${MODEL_1_PORT:-8000} \
        --gpu-memory-utilization ${MODEL_1_GPU_MEMORY:-0.9} \
        --max-model-len ${MODEL_1_MAX_LEN:-4096} \
        --enforce-eager \
        --compilation-config '{"mode": 0}' \
        --attention-backend FLASHINFER 2>&1 | \
        tee -a "$MODEL_1_LOG" | sed -u 's/^/[Model1] /') &

    PIDS+=($!)
    echo "[Model 1] Started with PID ${PIDS[-1]}"
else
    echo "[Model 1] Disabled or no path specified"
fi

# 모델 2 시작
if [ "${MODEL_2_ENABLED:-false}" = "true" ] && [ -n "$MODEL_2_PATH" ]; then
    echo ""
    echo "[Model 2] Starting on GPU ${MODEL_2_GPU:-1}..."
    echo "  Path: $MODEL_2_PATH"
    echo "  Port: ${MODEL_2_PORT:-8001}"
    echo "  GPU Memory: ${MODEL_2_GPU_MEMORY:-0.9}"
    echo "  Max Length: ${MODEL_2_MAX_LEN:-4096}"

    MODEL_2_LOG="$LOG_DIR/model2.log"
    echo "  Log File: $MODEL_2_LOG"

    (CUDA_VISIBLE_DEVICES=${MODEL_2_GPU:-1} vllm serve "$MODEL_2_PATH" \
        --host 0.0.0.0 \
        --port ${MODEL_2_PORT:-8001} \
        --gpu-memory-utilization ${MODEL_2_GPU_MEMORY:-0.9} \
        --max-model-len ${MODEL_2_MAX_LEN:-4096} \
        --enforce-eager \
        --compilation-config '{"mode": 0}' \
        --attention-backend FLASHINFER 2>&1 | \
        tee -a "$MODEL_2_LOG" | sed -u 's/^/[Model2] /') &

    PIDS+=($!)
    echo "[Model 2] Started with PID ${PIDS[-1]}"
else
    echo "[Model 2] Disabled or no path specified"
fi

echo ""
echo "=========================================="

# 실행 중인 프로세스가 없으면 종료
if [ ${#PIDS[@]} -eq 0 ]; then
    echo "ERROR: No models enabled. Set MODEL_1_ENABLED=true or MODEL_2_ENABLED=true"
    echo "=========================================="
    exit 1
fi

echo "Running ${#PIDS[@]} model(s)"
echo "PIDs: ${PIDS[*]}"
echo "=========================================="

# 시그널 핸들러 - 모든 자식 프로세스 종료
cleanup() {
    echo ""
    echo "Shutting down vLLM servers..."
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            echo "Stopping PID $pid..."
            kill -TERM "$pid" 2>/dev/null || true
        fi
    done
    wait
    echo "All servers stopped."
    exit 0
}

trap cleanup SIGTERM SIGINT

# 모든 프로세스가 종료될 때까지 대기
wait -n "${PIDS[@]}" 2>/dev/null || true

# 하나라도 종료되면 나머지도 종료
echo "One of the servers exited. Shutting down..."
cleanup
