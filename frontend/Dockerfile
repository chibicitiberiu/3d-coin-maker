# Unified Dockerfile for frontend with environment-specific configurations
# Build args control dev vs prod behavior

ARG ENVIRONMENT=development

# Development stage
FROM node:20-alpine AS development

# Set working directory
WORKDIR /app

# Install pnpm
RUN npm install -g pnpm@9.15.0

# Copy package files
COPY package*.json pnpm-lock.yaml ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy source code
COPY . .

# Expose port (will be set by environment variable)
EXPOSE 5173

# Start development server
CMD ["pnpm", "run", "dev"]

# Production builder stage
FROM node:20-alpine AS builder

# Install dumb-init for proper signal handling
RUN apk add --no-cache dumb-init

# Set working directory
WORKDIR /app

# Build arguments for environment variables
ARG ENVIRONMENT=development
ARG PUBLIC_API_BASE_URL

# Install pnpm globally with specific version for reproducibility
RUN npm install -g pnpm@9.15.0

# Copy package files first for better layer caching
COPY package.json pnpm-lock.yaml ./

# Install dependencies with frozen lockfile for reproducible builds
RUN pnpm install --frozen-lockfile --production=false

# Copy source code
COPY . .

# Set placeholder for runtime substitution
ENV PUBLIC_API_BASE_URL=__API_BASE_URL_PLACEHOLDER__

# Build the application with production optimizations
RUN pnpm run build

# Production runtime stage
FROM nginx:1.25-alpine AS production

# Install dumb-init and security updates
RUN apk add --no-cache dumb-init \
    && apk upgrade --no-cache

# Create nginx user if it doesn't exist
RUN addgroup -g 101 -S nginx || true \
    && adduser -S -D -H -u 101 -h /var/cache/nginx -s /sbin/nologin -G nginx -g nginx nginx || true

# Copy built files to nginx with proper permissions
COPY --from=builder --chown=nginx:nginx /build/frontend /usr/share/nginx/html

# Copy optimized nginx configuration
COPY --chown=nginx:nginx nginx.conf /etc/nginx/conf.d/default.conf

# Remove default nginx config
RUN rm -f /etc/nginx/conf.d/default.conf.bak

# Create startup script for environment substitution
RUN echo '#!/bin/sh' > /docker-entrypoint.sh && \
    echo 'set -e' >> /docker-entrypoint.sh && \
    echo '' >> /docker-entrypoint.sh && \
    echo '# Replace placeholder with actual API URL from environment' >> /docker-entrypoint.sh && \
    echo 'API_URL=${PUBLIC_API_BASE_URL:-http://localhost:8000}' >> /docker-entrypoint.sh && \
    echo 'find /usr/share/nginx/html -type f -name "*.js" -o -name "*.html" | while read file; do' >> /docker-entrypoint.sh && \
    echo '  if [ -f "$file" ]; then' >> /docker-entrypoint.sh && \
    echo '    sed -i "s|__API_BASE_URL_PLACEHOLDER__|$API_URL|g" "$file"' >> /docker-entrypoint.sh && \
    echo '  fi' >> /docker-entrypoint.sh && \
    echo 'done' >> /docker-entrypoint.sh && \
    echo '' >> /docker-entrypoint.sh && \
    echo '# Start nginx' >> /docker-entrypoint.sh && \
    echo 'exec dumb-init -- nginx -g "daemon off;"' >> /docker-entrypoint.sh && \
    chmod +x /docker-entrypoint.sh

# Create nginx directories with proper permissions
RUN mkdir -p /var/cache/nginx /var/log/nginx /var/run \
    && chown -R nginx:nginx /var/cache/nginx /var/log/nginx /var/run /etc/nginx

# Run nginx as root for now (typical in containers)
# USER nginx

# Expose port 80
EXPOSE 80

# Use our startup script
CMD ["/docker-entrypoint.sh"]

# Final stage selection based on environment
FROM ${ENVIRONMENT} AS final