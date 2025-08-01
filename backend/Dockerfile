# Multi-stage build for development

# Stage 1: Build HMM binary
FROM python:3.11-slim AS hmm-builder

# Install build dependencies for HMM
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    cmake \
    make \
    pkg-config \
    libglm-dev \
    && rm -rf /var/lib/apt/lists/*

# Build HMM from source
RUN cd /tmp && \
    git clone https://github.com/fogleman/hmm.git && \
    cd hmm && \
    make && \
    cp hmm /usr/local/bin/hmm

# Stage 2: Development runtime
FROM python:3.11-slim

# Install runtime dependencies (including curl for health checks and wget for dev convenience)
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy HMM binary from builder stage
COPY --from=hmm-builder /usr/local/bin/hmm /usr/local/bin/hmm

# Install Poetry
RUN pip install poetry

# Set working directory
WORKDIR /app

# Copy poetry files
COPY pyproject.toml poetry.lock ./

# Configure poetry and install all dependencies (including dev)
RUN poetry config virtualenvs.create false \
    && poetry install

# Copy application code
COPY . .

# Accept UID/GID as build arguments (default to 1000 if not provided)
ARG UID=1000
ARG GID=1000

# Accept USE_CELERY as build argument (default to true for development)
ARG USE_CELERY=true

# Create a non-root user with matching UID/GID
RUN groupadd -g $GID appuser && useradd -u $UID -g $GID -m appuser

# Create temp directory with proper permissions
RUN mkdir -p temp && chmod 755 temp && chown -R appuser:appuser /app

# Set USE_CELERY environment variable from build argument
ENV USE_CELERY=${USE_CELERY}

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Default command for development
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]