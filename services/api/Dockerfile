FROM python:3.12-slim

WORKDIR /workspace

# Install system dependencies (curl for healthcheck, build-essential for any C-extensions)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast, deterministic dependency resolution
RUN pip install --no-cache-dir uv

# Copy project workspace packages and reference data
COPY pipeline /workspace/pipeline
COPY services/api /workspace/services/api
COPY contracts /workspace/contracts
COPY data/fixtures /workspace/data/fixtures
COPY data/reference /workspace/data/reference

WORKDIR /workspace/services/api

# Install dependencies using uv into system environment
RUN uv pip install --system -e /workspace/pipeline -e /workspace/services/api

# Default environment configuration
ENV PYTHONUNBUFFERED=1 \
    DATA_DIR=/workspace/data/fixtures \
    REFERENCE_DIR=/workspace/data/reference \
    WEB_ORIGIN=http://localhost:3000 \
    LLM_PROVIDER=replay \
    PORT=8000

EXPOSE 8000

# Container healthcheck querying FastAPI /api/health
HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f "http://localhost:${PORT}/api/health" || exit 1

# Launch uvicorn dynamically bound to $PORT for local and cloud host compatibility
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
