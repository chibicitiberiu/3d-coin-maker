FROM python:3.11-slim

# Install system dependencies including OpenSCAD, hmm, and manifold3d requirements
RUN apt-get update && apt-get install -y \
    openscad \
    curl \
    git \
    wget \
    build-essential \
    pkg-config \
    libpython3-dev \
    python3-distutils \
    libglm-dev \
    make \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# Build and install hmm (heightmap meshing utility) from source
RUN cd /tmp && \
    git clone https://github.com/fogleman/hmm.git && \
    cd hmm && \
    make && \
    cp hmm /usr/local/bin/ && \
    cd / && \
    rm -rf /tmp/hmm

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

# Create a non-root user with matching UID/GID
RUN groupadd -g $GID appuser && useradd -u $UID -g $GID -m appuser

# Create temp directory with proper permissions
RUN mkdir -p temp && chmod 755 temp && chown -R appuser:appuser /app

# Verify OpenSCAD is installed
RUN openscad --version

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Default command for development
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]