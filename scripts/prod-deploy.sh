#!/bin/bash

# Production deployment script
echo "Deploying Coin Maker in production mode..."

# Check if production config exists
if [ ! -f "config/backend.env" ]; then
    echo "❌ Production config file config/backend.env not found!"
    echo "Please create it based on config/backend.dev.env"
    exit 1
fi

# Warn about production deployment
echo "⚠️  PRODUCTION DEPLOYMENT"
echo "Make sure you have:"
echo "1. Updated SECRET_KEY in config/backend.env"
echo "2. Set proper ALLOWED_HOSTS"
echo "3. Configured SSL certificates if needed"
echo "4. Reviewed all production settings"
echo ""
read -p "Continue with production deployment? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 1
fi

# Stop any existing services
echo "Stopping existing services..."
docker compose down --remove-orphans

# Build and start production services
echo "Building and starting production services..."
docker compose up -d --build

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Check if backend is healthy
echo "Checking backend health..."
for i in {1..30}; do
    if curl -f http://localhost:8000/api/health/ >/dev/null 2>&1; then
        echo "✅ Backend is healthy!"
        break
    fi
    echo "Waiting for backend... ($i/30)"
    sleep 2
done

# Show status
echo ""
echo "🚀 Production deployment complete!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo ""
echo "Check logs with: docker compose logs -f"
echo "Stop services with: docker compose down"