#!/bin/bash
set -e

# Create log directory if it doesn't exist
mkdir -p /logs

# Generate timestamp-based log filename
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/logs/mlflow_${TIMESTAMP}.log"

echo "Starting MLflow server..."
echo "Logs will be written to: ${LOG_FILE}"

# Start MLflow server and redirect logs to both console and file
mlflow server \
    --backend-store-uri "${MLFLOW_BACKEND_STORE_URI}" \
    --default-artifact-root "${MLFLOW_DEFAULT_ARTIFACT_ROOT:-s3://mlflow/artifacts}" \
    --host 0.0.0.0 \
    --port 5000 \
    > >(tee -a "${LOG_FILE}") 2> >(tee -a "${LOG_FILE}" >&2) &

# Store the PID
MLFLOW_PID=$!

# Wait for MLflow to be ready
echo "Waiting for MLflow server to be ready..."
for i in {1..30}; do
    if curl -f http://localhost:5000/health > /dev/null 2>&1; then
        echo "MLflow server is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "MLflow server failed to start within 30 seconds"
        exit 1
    fi
    sleep 1
done

# Keep the script running and forward signals
trap "kill ${MLFLOW_PID}" SIGTERM SIGINT
wait ${MLFLOW_PID}
