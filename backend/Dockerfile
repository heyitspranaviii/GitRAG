FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy ONLY dependency file first (layer caching)
COPY pyproject.toml ./

# Install CPU-only torch FIRST to prevent CUDA downloads
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies (cached if pyproject.toml unchanged)
RUN pip install --no-cache-dir . && \
    pip install --no-cache-dir semgrep

# Copy source code AFTER dependencies
COPY gitrag/ ./gitrag/

# Create runtime directories
RUN mkdir -p /app/data/chroma /app/data/memory /app/data/repos /app/logs /app/.cache/huggingface

# Non-root user FIRST, then set permissions
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

ENV HF_HOME=/app/.cache/huggingface

USER appuser

EXPOSE 8000

CMD ["uvicorn", "gitrag.api.server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]