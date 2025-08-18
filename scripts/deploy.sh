#!/bin/bash

# Business Systems Integration Platform - Deployment Script
# Usage: ./deploy.sh [environment] [version]
# Example: ./deploy.sh production v1.0.0

set -e  # Exit on any error

# Configuration
ENVIRONMENT=${1:-development}
VERSION=${2:-latest}
PROJECT_NAME="business-systems-platform"
DOCKER_REGISTRY="your-registry.com"  # Replace with your registry
BACKUP_DIR="./backups"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if environment file exists
    if [[ "$ENVIRONMENT" == "production" ]] && [[ ! -f ".env.production" ]]; then
        log_error "Production environment file (.env.production) not found."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Backup existing data
backup_data() {
    if [[ "$ENVIRONMENT" == "production" ]]; then
        log_info "Creating backup..."
        
        mkdir -p "$BACKUP_DIR"
        BACKUP_NAME="backup_$(date +%Y%m%d_%H%M%S)"
        
        # Backup database
        docker-compose exec postgres pg_dump -U admin business_platform > "$BACKUP_DIR/${BACKUP_NAME}_db.sql"
        
        # Backup Redis data
        docker-compose exec redis redis-cli --rdb "$BACKUP_DIR/${BACKUP_NAME}_redis.rdb"
        
        # Backup configuration files
        tar -czf "$BACKUP_DIR/${BACKUP_NAME}_config.tar.gz" .env* docker-compose*.yml
        
        log_success "Backup created: $BACKUP_NAME"
    fi
}

# Build application images
build_images() {
    log_info "Building application images..."
    
    # Build backend image
    log_info "Building backend image..."
    docker build -t "${PROJECT_NAME}-backend:${VERSION}" \
        -f backend/Dockerfile \
        --build-arg VERSION="$VERSION" \
        --build-arg ENVIRONMENT="$ENVIRONMENT" \
        ./backend
    
    # Build frontend image
    log_info "Building frontend image..."
    docker build -t "${PROJECT_NAME}-frontend:${VERSION}" \
        -f frontend/Dockerfile \
        --build-arg VERSION="$VERSION" \
        --build-arg ENVIRONMENT="$ENVIRONMENT" \
        ./frontend
    
    log_success "Images built successfully"
}

# Run tests
run_tests() {
    log_info "Running tests..."
    
    # Backend tests
    log_info "Running backend tests..."
    cd backend
    python -m pytest tests/ -v --cov=app --cov-report=term-missing
    cd ..
    
    # Frontend tests
    log_info "Running frontend tests..."
    cd frontend
    npm test -- --coverage --watchAll=false
    cd ..
    
    log_success "All tests passed"
}

# Deploy infrastructure services
deploy_infrastructure() {
    log_info "Deploying infrastructure services..."
    
    # Copy environment file
    if [[ -f ".env.${ENVIRONMENT}" ]]; then
        cp ".env.${ENVIRONMENT}" .env
        log_info "Using environment configuration: .env.${ENVIRONMENT}"
    fi
    
    # Start infrastructure services
    docker-compose up -d zookeeper kafka redis postgres pgadmin kafka-ui
    
    # Wait for services to be ready
    log_info "Waiting for infrastructure services to be ready..."
    sleep 30
    
    # Check service health
    check_service_health "postgres" "5432"
    check_service_health "redis" "6379"
    check_service_health "kafka" "9092"
    
    log_success "Infrastructure services deployed"
}

# Deploy application services
deploy_application() {
    log_info "Deploying application services..."
    
    # Create Docker Compose override for the environment
    create_compose_override
    
    # Start application services
    docker-compose -f docker-compose.yml -f docker-compose.${ENVIRONMENT}.yml up -d backend frontend
    
    # Wait for services to be ready
    log_info "Waiting for application services to be ready..."
    sleep 20
    
    # Check application health
    check_application_health
    
    log_success "Application services deployed"
}

# Create Docker Compose override file
create_compose_override() {
    log_info "Creating Docker Compose override for ${ENVIRONMENT}..."
    
    cat > "docker-compose.${ENVIRONMENT}.yml" << EOF
version: '3.8'

services:
  backend:
    image: ${PROJECT_NAME}-backend:${VERSION}
    environment:
      - ENVIRONMENT=${ENVIRONMENT}
      - VERSION=${VERSION}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  frontend:
    image: ${PROJECT_NAME}-frontend:${VERSION}
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
      - ENVIRONMENT=${ENVIRONMENT}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
EOF
    
    log_success "Docker Compose override created"
}

# Check service health
check_service_health() {
    local service_name=$1
    local port=$2
    local max_attempts=30
    local attempt=1
    
    log_info "Checking health of $service_name..."
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose exec $service_name sh -c "nc -z localhost $port" &> /dev/null; then
            log_success "$service_name is healthy"
            return 0
        fi
        
        log_info "Attempt $attempt/$max_attempts: $service_name not ready yet..."
        sleep 10
        ((attempt++))
    done
    
    log_error "$service_name failed to become healthy"
    return 1
}

# Check application health
check_application_health() {
    local max_attempts=30
    local attempt=1
    
    log_info "Checking application health..."
    
    while [ $attempt -le $max_attempts ]; do
        # Check backend health
        if curl -f http://localhost:8000/health &> /dev/null; then
            log_success "Backend is healthy"
            break
        fi
        
        log_info "Attempt $attempt/$max_attempts: Backend not ready yet..."
        sleep 10
        ((attempt++))
        
        if [ $attempt -gt $max_attempts ]; then
            log_error "Backend failed health check"
            return 1
        fi
    done
    
    # Check frontend health
    attempt=1
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:3000 &> /dev/null; then
            log_success "Frontend is healthy"
            return 0
        fi
        
        log_info "Attempt $attempt/$max_attempts: Frontend not ready yet..."
        sleep 10
        ((attempt++))
        
        if [ $attempt -gt $max_attempts ]; then
            log_error "Frontend failed health check"
            return 1
        fi
    done
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    # Wait for database to be ready
    sleep 10
    
    # Run migrations
    docker-compose exec backend python -m alembic upgrade head
    
    log_success "Database migrations completed"
}

# Setup monitoring
setup_monitoring() {
    if [[ "$ENVIRONMENT" == "production" ]]; then
        log_info "Setting up monitoring..."
        
        # Start monitoring services (if configured)
        # docker-compose -f docker-compose.monitoring.yml up -d
        
        log_info "Monitoring setup completed"
    fi
}

# Cleanup old images
cleanup_old_images() {
    log_info "Cleaning up old Docker images..."
    
    # Remove old images (keep last 3 versions)
    docker images "${PROJECT_NAME}-backend" --format "table {{.Tag}}" | tail -n +4 | xargs -r docker rmi "${PROJECT_NAME}-backend:" &> /dev/null || true
    docker images "${PROJECT_NAME}-frontend" --format "table {{.Tag}}" | tail -n +4 | xargs -r docker rmi "${PROJECT_NAME}-frontend:" &> /dev/null || true
    
    # Clean up dangling images
    docker image prune -f
    
    log_success "Cleanup completed"
}

# Rollback function
rollback() {
    log_warning "Initiating rollback..."
    
    # Stop current services
    docker-compose down
    
    # Restore from backup if available
    if [[ -n "$BACKUP_NAME" ]]; then
        log_info "Restoring from backup: $BACKUP_NAME"
        # Restore database
        docker-compose up -d postgres
        sleep 20
        docker-compose exec postgres psql -U admin -d business_platform < "$BACKUP_DIR/${BACKUP_NAME}_db.sql"
        
        # Restore Redis
        docker-compose up -d redis
        sleep 10
        docker cp "$BACKUP_DIR/${BACKUP_NAME}_redis.rdb" $(docker-compose ps -q redis):/data/dump.rdb
        docker-compose restart redis
    fi
    
    log_warning "Rollback completed"
}

# Main deployment function
main() {
    log_info "Starting deployment for environment: $ENVIRONMENT, version: $VERSION"
    
    # Trap errors and rollback
    trap 'log_error "Deployment failed. Initiating rollback..."; rollback; exit 1' ERR
    
    check_prerequisites
    backup_data
    build_images
    run_tests
    deploy_infrastructure
    run_migrations
    deploy_application
    setup_monitoring
    cleanup_old_images
    
    log_success "Deployment completed successfully!"
    log_info "Application is available at:"
    log_info "  Frontend: http://localhost:3000"
    log_info "  Backend API: http://localhost:8000"
    log_info "  API Docs: http://localhost:8000/docs"
    log_info "  Kafka UI: http://localhost:8080"
    log_info "  pgAdmin: http://localhost:5050"
}

# Show usage
show_usage() {
    echo "Usage: $0 [environment] [version]"
    echo ""
    echo "Environments: development, staging, production"
    echo "Version: any valid version tag (default: latest)"
    echo ""
    echo "Examples:"
    echo "  $0                          # Deploy development with latest"
    echo "  $0 production v1.0.0        # Deploy production with v1.0.0"
    echo "  $0 staging                  # Deploy staging with latest"
}

# Handle command line arguments
case "$1" in
    -h|--help)
        show_usage
        exit 0
        ;;
    "")
        main
        ;;
    *)
        if [[ "$1" =~ ^(development|staging|production)$ ]]; then
            main
        else
            log_error "Invalid environment: $1"
            show_usage
            exit 1
        fi
        ;;
esac