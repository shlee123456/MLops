FROM nvidia/cuda:12.1.0-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create symbolic links
RUN ln -s /usr/bin/python3 /usr/bin/python

# Install PyTorch with CUDA support
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install training dependencies
RUN pip install --no-cache-dir \
    transformers==4.36.0 \
    accelerate==0.25.0 \
    peft==0.7.1 \
    bitsandbytes==0.41.3 \
    datasets==2.15.0 \
    mlflow==2.8.0 \
    structlog==23.2.0 \
    sentencepiece \
    protobuf

# Copy application code
COPY src/ /app/src/
COPY data/ /app/data/

# Create directories
RUN mkdir -p /logs /models

# Set environment variables for logging
ENV LOG_LEVEL=INFO
ENV LOG_FORMAT=json

CMD ["bash"]
