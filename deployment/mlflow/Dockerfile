FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install MLflow and dependencies
RUN pip install --no-cache-dir \
    mlflow==2.8.0 \
    psycopg2-binary \
    boto3

# Create log directory
RUN mkdir -p /logs

# Copy entrypoint script
COPY deployment/mlflow/start-mlflow.sh /app/start-mlflow.sh
RUN chmod +x /app/start-mlflow.sh

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

EXPOSE 5000

ENTRYPOINT ["/app/start-mlflow.sh"]
