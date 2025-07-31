#!/bin/bash

# Environment Setup Script for Coin Maker
# This script helps configure environment variables for dev/prod deployments

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to generate a secure random secret key
generate_secret_key() {
    python3 -c "import secrets; print(secrets.token_urlsafe(50))"
}

# Function to setup development environment
setup_dev() {
    print_info "Setting up development environment..."
    
    # Check if development config exists
    if [[ ! -f "$PROJECT_ROOT/config/backend.dev.env" ]]; then
        print_error "Development backend config not found!"
        exit 1
    fi
    
    if [[ ! -f "$PROJECT_ROOT/config/frontend.dev.env" ]]; then
        print_error "Development frontend config not found!"
        exit 1
    fi
    
    # Create symlinks for development
    ln -sf "$PROJECT_ROOT/config/backend.dev.env" "$PROJECT_ROOT/config/backend.env"
    ln -sf "$PROJECT_ROOT/config/frontend.dev.env" "$PROJECT_ROOT/config/frontend.env"
    
    print_success "Development environment configured!"
    print_info "Features enabled:"
    echo "  - Rate limiting: DISABLED"
    echo "  - Security headers: DISABLED"
    echo "  - Debug mode: ENABLED"
    echo "  - CORS: Allow all origins"
    echo "  - File size limit: 100MB"
    echo "  - Verbose logging: ENABLED"
}

# Function to setup production environment
setup_prod() {
    print_info "Setting up production environment..."
    
    # Check if production config exists
    if [[ ! -f "$PROJECT_ROOT/config/backend.env" ]]; then
        print_error "Production backend config not found!"
        exit 1
    fi
    
    if [[ ! -f "$PROJECT_ROOT/config/frontend.env" ]]; then
        print_error "Production frontend config not found!"
        exit 1
    fi
    
    # Check if secret key is still default
    if grep -q "change-this-in-production" "$PROJECT_ROOT/config/backend.env"; then
        print_warning "Production secret key is still default!"
        print_info "Generating new secret key..."
        
        NEW_SECRET=$(generate_secret_key)
        
        # Update secret key in production config
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s|SECRET_KEY=change-this-in-production-with-secure-random-key|SECRET_KEY=$NEW_SECRET|" "$PROJECT_ROOT/config/backend.env"
        else
            # Linux
            sed -i "s|SECRET_KEY=change-this-in-production-with-secure-random-key|SECRET_KEY=$NEW_SECRET|" "$PROJECT_ROOT/config/backend.env"
        fi
        
        print_success "Generated new production secret key!"
    fi
    
    # Validate production domain
    if grep -q "coin-maker.example.com" "$PROJECT_ROOT/config/backend.env"; then
        print_warning "Production domain is still example.com!"
        print_info "Please update ALLOWED_HOSTS and CORS_ALLOWED_ORIGINS in config/backend.env"
    fi
    
    print_success "Production environment configured!"
    print_info "Features enabled:"
    echo "  - Rate limiting: ENABLED"
    echo "  - Security headers: ENABLED"
    echo "  - Debug mode: DISABLED"
    echo "  - CORS: Restricted origins"
    echo "  - File size limit: 50MB"
    echo "  - SSL security: ENABLED"
}

# Function to validate environment
validate_env() {
    print_info "Validating environment configuration..."
    
    # Check Docker and Docker Compose
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed!"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed!"
        exit 1
    fi
    
    # Check required config files exist
    required_files=(
        "config/backend.env"
        "config/frontend.env"
        "docker-compose.yml"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$PROJECT_ROOT/$file" ]]; then
            print_error "Required file missing: $file"
            exit 1
        fi
    done
    
    print_success "Environment validation passed!"
}

# Function to show help
show_help() {
    echo "Coin Maker Environment Setup Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  dev      Setup development environment"
    echo "  prod     Setup production environment"
    echo "  validate Validate environment configuration"
    echo "  help     Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 dev       # Setup for development"
    echo "  $0 prod      # Setup for production"
    echo "  $0 validate  # Check environment"
}

# Main script logic
case "${1:-help}" in
    "dev")
        setup_dev
        validate_env
        ;;
    "prod")
        setup_prod
        validate_env
        ;;
    "validate")
        validate_env
        ;;
    "help"|*)
        show_help
        ;;
esac

print_info "Setup complete! You can now run:"
echo "  Development: docker-compose -f docker-compose.dev.yml up"
echo "  Production:  docker-compose up"