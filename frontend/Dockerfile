# Multi-stage build for production frontend
FROM node:20-alpine AS builder

# Install dumb-init for proper signal handling
RUN apk add --no-cache dumb-init

# Set working directory
WORKDIR /app

# Install pnpm globally with specific version for reproducibility
RUN npm install -g pnpm@8.15.0

# Copy package files first for better layer caching
COPY package.json pnpm-lock.yaml ./

# Install dependencies with frozen lockfile for reproducible builds
RUN pnpm install --frozen-lockfile --production=false

# Copy source code
COPY . .

# Build the application with production optimizations
RUN pnpm run build

# Production stage with nginx
FROM nginx:1.25-alpine

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

# Add health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1

# Switch to non-root user
USER nginx

# Expose port 80
EXPOSE 80

# Use dumb-init for proper signal handling
ENTRYPOINT ["dumb-init", "--"]

# Start nginx with optimized settings
CMD ["nginx", "-g", "daemon off; error_log /var/log/nginx/error.log warn;"]