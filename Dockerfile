# syntax=docker/dockerfile:1.7
# Multi-stage build for chainplate

ARG PYTHON_VERSION=3.11
ARG UV_VERSION=0.4.18
FROM python:${PYTHON_VERSION}-slim AS base
ARG UV_VERSION

# Set up environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=0 \
    CHAINPLATE_DB=/data/chainplate.db \
    CHAINPLATE_PORT=5000

# System deps (nodejs/npm for npx, plus curl for uv installer)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates nodejs npm && \
    rm -rf /var/lib/apt/lists/*

# Install uv (provides `uv` and `uvx`)
RUN set -eux; \
    VER="${UV_VERSION:-0.4.18}"; \
    case "$VER" in v*) TAG="$VER" ;; *) TAG="v$VER" ;; esac; \
    curl -LsSf https://astral.sh/uv/install.sh | sh -s -- "$TAG"; \
    ln -s /root/.local/bin/uv /usr/local/bin/uv
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app
# ...existing code...
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
# ...existing code...
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY examples ./examples
# ...existing code...
RUN python -m pip install --no-cache-dir build && \
    python -m build --wheel && \
    pip install --no-cache-dir dist/*.whl && \
    rm -rf dist build
# ...existing code...
RUN mkdir -p /data && chown -R 1000:1000 /data
# ...existing code...
RUN useradd -m -u 1000 chainplate
USER chainplate
# ...existing code...
EXPOSE 5000
VOLUME ["/data"]
ENTRYPOINT ["python", "-m", "chainplate.modes.chainplate_server"]
CMD ["--port", "5000"]