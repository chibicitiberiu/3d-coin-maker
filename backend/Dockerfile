# Unified Dockerfile for backend with environment-specific configurations
# Build args control dev vs prod behavior

# Stage 1: Build HMM binary (common for both environments)
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

# Stage 2: Runtime environment
FROM python:3.11-slim

# Build arguments for environment-specific configuration
ARG ENVIRONMENT=development
ARG UID=1000
ARG GID=1000
ARG USE_CELERY=true

# Copy HMM binary from builder stage
COPY --from=hmm-builder /usr/local/bin/hmm /usr/local/bin/hmm

# Install base dependencies
RUN apt-get update && apt-get install -y \
    curl \
    $([ "$ENVIRONMENT" = "production" ] && echo "dumb-init") \
    $([ "$ENVIRONMENT" = "development" ] && echo "wget") \
    && rm -rf /var/lib/apt/lists/*

# Install build dependencies for production (will be removed later)
RUN if [ "$ENVIRONMENT" = "production" ]; then \
    apt-get update && apt-get install -y \
        build-essential \
        libpython3-dev \
        python3-distutils \
        && rm -rf /var/lib/apt/lists/*; \
    fi

# Install Poetry
RUN pip install poetry

# Set working directory
WORKDIR /app

# Copy poetry files
COPY pyproject.toml poetry.lock ./

# Configure poetry and install dependencies based on environment
RUN poetry config virtualenvs.create false && \
    if [ "$ENVIRONMENT" = "production" ]; then \
        poetry install --only=main; \
    else \
        poetry install; \
    fi

# Production optimizations: remove build dependencies and install production servers
RUN if [ "$ENVIRONMENT" = "production" ]; then \
        apt-get remove -y build-essential libpython3-dev python3-distutils && \
        apt-get autoremove -y && \
        apt-get clean && \
        rm -rf /var/lib/apt/lists/* && \
        pip uninstall -y poetry && \
        pip install --no-cache-dir \
            gunicorn==21.2.0 \
            uvicorn[standard]==0.35.0 \
            redis==5.0.1 \
            celery==5.3.4; \
    fi

# Copy application code
COPY . .

# Create directories with proper permissions
RUN if [ "$ENVIRONMENT" = "production" ]; then \
        mkdir -p /app/temp /app/data /app/static /app/logs && \
        chmod 755 /app/temp /app/data /app/static /app/logs; \
    else \
        mkdir -p temp && chmod 755 temp; \
    fi

# Create user (use consistent name for both environments)
RUN if [ "$ENVIRONMENT" = "production" ]; then \
        groupadd -r appuser && useradd -r -g appuser -d /app -s /bin/bash appuser; \
    else \
        groupadd -g $GID appuser && useradd -u $UID -g $GID -m appuser; \
    fi

# Set ownership 
RUN chown -R appuser:appuser /app

# Set environment variables
ENV USE_CELERY=${USE_CELERY}
ENV PYTHONPATH=/app/

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check for production
RUN if [ "$ENVIRONMENT" = "production" ]; then \
        echo '#!/bin/sh' > /tmp/healthcheck.sh && \
        echo 'curl -f http://localhost:8000/api/health/ || exit 1' >> /tmp/healthcheck.sh && \
        chmod +x /tmp/healthcheck.sh; \
    fi

# For development, use simple entrypoint (production would need dumb-init)

CMD if [ "$ENVIRONMENT" = "production" ]; then \
        exec gunicorn \
            --bind 0.0.0.0:8000 \
            --workers 3 \
            --worker-class uvicorn.workers.UvicornWorker \
            --worker-connections 1000 \
            --max-requests 1000 \
            --max-requests-jitter 100 \
            --timeout 120 \
            --keep-alive 5 \
            --preload \
            --access-logfile /app/logs/access.log \
            --error-logfile /app/logs/error.log \
            --capture-output \
            fastapi_main:app; \
    else \
        exec python -m uvicorn fastapi_main:app --host 0.0.0.0 --port 8000 --reload; \
    fi