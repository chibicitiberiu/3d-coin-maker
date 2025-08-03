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

# Install pnpm globally with specific version for reproducibility
RUN npm install -g pnpm@9.15.0

# Copy package files first for better layer caching
COPY package.json pnpm-lock.yaml ./

# Install dependencies with frozen lockfile for reproducible builds
RUN pnpm install --frozen-lockfile --production=false

# Copy source code
COPY . .

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
COPY --from=builder --chown=nginx:nginx /app/build /usr/share/nginx/html

# Copy optimized nginx configuration
COPY --chown=nginx:nginx nginx.conf /etc/nginx/conf.d/default.conf

# Remove default nginx config
RUN rm -f /etc/nginx/conf.d/default.conf.bak

# Create nginx directories with proper permissions
RUN mkdir -p /var/cache/nginx /var/log/nginx /var/run \
    && chown -R nginx:nginx /var/cache/nginx /var/log/nginx /var/run /etc/nginx

# Switch to non-root user
USER nginx

# Expose port 80
EXPOSE 80

# Use dumb-init for proper signal handling
ENTRYPOINT ["dumb-init", "--"]

# Start nginx with optimized settings
CMD ["nginx", "-g", "daemon off; error_log /var/log/nginx/error.log warn;"]

# Final stage selection based on environment
FROM ${ENVIRONMENT} AS final