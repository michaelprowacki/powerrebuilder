# Multi-stage Dockerfile for PowerRebuilder
# Optimized for both development and production use

# Stage 1: Base dependencies
FROM python:3.13-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Create non-root user
RUN useradd -m -u 1000 powerrebuilder && \
    mkdir -p /app && \
    chown -R powerrebuilder:powerrebuilder /app

WORKDIR /app

# Stage 2: Dependencies
FROM base AS dependencies

# Copy dependency files
COPY --chown=powerrebuilder:powerrebuilder pyproject.toml uv.lock ./

# Install dependencies as root for system packages
USER root
RUN uv sync --frozen --no-dev --no-install-project

# Stage 3: Development
FROM dependencies AS development

# Install all dependencies including dev
RUN uv sync --frozen --all-extras

# Copy source code
COPY --chown=powerrebuilder:powerrebuilder . .

# Switch to non-root user
USER powerrebuilder

# Development entrypoint
CMD ["uv", "run", "python", "-m", "ipython"]

# Stage 4: Testing
FROM dependencies AS testing

# Install test dependencies
RUN uv sync --frozen --extra test

# Copy source code and tests
COPY --chown=powerrebuilder:powerrebuilder src/ ./src/
COPY --chown=powerrebuilder:powerrebuilder tests/ ./tests/
COPY --chown=powerrebuilder:powerrebuilder pyproject.toml ./

# Switch to non-root user
USER powerrebuilder

# Run tests
CMD ["uv", "run", "pytest", "tests/", "-v"]

# Stage 5: Builder
FROM dependencies AS builder

# Copy source code
COPY --chown=powerrebuilder:powerrebuilder src/ ./src/
COPY --chown=powerrebuilder:powerrebuilder pyproject.toml README.md LICENSE ./

# Build the package
RUN uv build --wheel

# Stage 6: Production runtime
FROM python:3.13-slim AS production

# Set environment variables for production
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONOPTIMIZE=2 \
    UV_SYSTEM_PYTHON=1

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for runtime
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Create non-root user
RUN useradd -m -u 1000 powerrebuilder && \
    mkdir -p /app /data && \
    chown -R powerrebuilder:powerrebuilder /app /data

WORKDIR /app

# Copy built wheel from builder
COPY --from=builder --chown=powerrebuilder:powerrebuilder /app/dist/*.whl ./

# Install the application
RUN uv pip install --system *.whl && \
    rm -rf *.whl

# Switch to non-root user
USER powerrebuilder

# Create volume mount points
VOLUME ["/data"]

# Expose port if needed (adjust based on your application)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD powerrebuilder --version || exit 1

# Production entrypoint
ENTRYPOINT ["powerrebuilder"]
CMD ["--help"]

# Stage 7: Production with debugging tools (optional)
FROM production AS production-debug

USER root

# Install debugging tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    vim \
    less \
    htop \
    strace \
    && rm -rf /var/lib/apt/lists/*

# Install Python debugging tools
RUN uv pip install --system \
    ipython \
    ipdb \
    py-spy \
    memray

USER powerrebuilder

# Override entrypoint for debugging
ENTRYPOINT ["/bin/bash"]
