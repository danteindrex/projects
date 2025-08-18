#!/bin/bash

# Business Systems Integration Platform - Development Setup Script
# Usage: ./setup-dev.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    local missing_tools=()
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        missing_tools+=("Docker")
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        missing_tools+=("Docker Compose")
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        missing_tools+=("Node.js")
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        missing_tools+=("Python 3")
    fi
    
    # Check Git
    if ! command -v git &> /dev/null; then
        missing_tools+=("Git")
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_info "Please install the missing tools and run this script again."
        exit 1
    fi
    
    log_success "All prerequisites are installed"
}

# Setup environment files
setup_environment() {
    log_info "Setting up environment files..."
    
    # Create .env file from example if it doesn't exist
    if [ ! -f .env ]; then
        if [ -f backend/env.example ]; then
            cp backend/env.example .env
            log_info "Created .env from backend/env.example"
        else
            log_warning "No env.example file found. Creating basic .env file..."
            cat > .env << EOF
# Database
DATABASE_URL=postgresql://admin:password123@localhost:5432/business_platform

# Redis
REDIS_URL=redis://localhost:6379

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_PREFIX=business_platform

# Security
SECRET_KEY=dev_secret_key_change_in_production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Configuration
API_V1_STR=/api/v1
CORS_ORIGINS=["http://localhost:3000"]
ALLOWED_HOSTS=["localhost", "127.0.0.1"]

# Development settings
DEBUG=true
ENVIRONMENT=development
LOG_LEVEL=DEBUG

# Rate limiting
RATE_LIMIT_PER_MINUTE=60

# External APIs (add your keys)
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
EOF
        fi
        
        log_warning "Please update .env file with your actual configuration values"
    else
        log_info ".env file already exists"
    fi
    
    # Create development environment file
    if [ ! -f .env.development ]; then
        cp .env .env.development
        log_info "Created .env.development"
    fi
    
    log_success "Environment files setup completed"
}

# Setup backend
setup_backend() {
    log_info "Setting up backend..."
    
    cd backend
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        log_info "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment and install dependencies
    log_info "Installing Python dependencies..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    log_success "Backend setup completed"
    cd ..
}

# Setup frontend
setup_frontend() {
    log_info "Setting up frontend..."
    
    cd frontend
    
    # Install Node.js dependencies
    log_info "Installing Node.js dependencies..."
    npm install
    
    # Run build to check everything is working
    log_info "Building frontend to verify setup..."
    npm run build
    
    log_success "Frontend setup completed"
    cd ..
}

# Setup Docker environment
setup_docker() {
    log_info "Setting up Docker environment..."
    
    # Pull required Docker images
    log_info "Pulling Docker images..."
    docker-compose pull
    
    # Build custom images
    log_info "Building custom Docker images..."
    docker-compose build
    
    log_success "Docker environment setup completed"
}

# Start infrastructure services
start_infrastructure() {
    log_info "Starting infrastructure services..."
    
    # Start infrastructure services only
    docker-compose up -d zookeeper kafka redis postgres pgadmin kafka-ui
    
    log_info "Waiting for services to start..."
    sleep 30
    
    # Check if services are running
    if docker-compose ps | grep -q "Up"; then
        log_success "Infrastructure services started successfully"
        
        log_info "Service URLs:"
        log_info "  PostgreSQL: localhost:5432 (admin:password123)"
        log_info "  Redis: localhost:6379"
        log_info "  Kafka: localhost:9092"
        log_info "  pgAdmin: http://localhost:5050 (admin@example.com:admin123)"
        log_info "  Kafka UI: http://localhost:8080"
    else
        log_warning "Some services may not have started correctly"
    fi
}

# Setup database
setup_database() {
    log_info "Setting up database..."
    
    # Wait for PostgreSQL to be ready
    log_info "Waiting for PostgreSQL to be ready..."
    sleep 10
    
    # Check if we can connect to the database
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose exec postgres pg_isready -U admin -d business_platform &> /dev/null; then
            log_success "PostgreSQL is ready"
            break
        fi
        
        log_info "Attempt $attempt/$max_attempts: PostgreSQL not ready yet..."
        sleep 5
        ((attempt++))
        
        if [ $attempt -gt $max_attempts ]; then
            log_error "PostgreSQL failed to start"
            return 1
        fi
    done
    
    # Run database migrations (if backend is set up with Alembic)
    if [ -f "backend/alembic.ini" ]; then
        log_info "Running database migrations..."
        cd backend
        source venv/bin/activate
        alembic upgrade head
        cd ..
    else
        log_info "No Alembic configuration found, skipping migrations"
    fi
    
    log_success "Database setup completed"
}

# Create Dockerfiles if they don't exist
create_dockerfiles() {
    log_info "Creating Dockerfiles..."
    
    # Backend Dockerfile
    if [ ! -f "backend/Dockerfile" ]; then
        cat > backend/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
EOF
        log_info "Created backend/Dockerfile"
    fi
    
    # Frontend Dockerfile
    if [ ! -f "frontend/Dockerfile" ]; then
        cat > frontend/Dockerfile << 'EOF'
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy application code
COPY . .

# Build the application
RUN npm run build

# Expose port
EXPOSE 3000

# Start application
CMD ["npm", "start"]
EOF
        log_info "Created frontend/Dockerfile"
    fi
    
    log_success "Dockerfiles created"
}

# Setup Git hooks
setup_git_hooks() {
    if [ -d ".git" ]; then
        log_info "Setting up Git hooks..."
        
        # Pre-commit hook
        cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash

echo "Running pre-commit checks..."

# Check if backend tests pass
cd backend
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    if ! python -m pytest tests/ -v; then
        echo "Backend tests failed. Commit aborted."
        exit 1
    fi
fi
cd ..

# Check if frontend builds successfully
cd frontend
if [ -f "package.json" ]; then
    if ! npm run build; then
        echo "Frontend build failed. Commit aborted."
        exit 1
    fi
fi
cd ..

echo "Pre-commit checks passed."
EOF
        
        chmod +x .git/hooks/pre-commit
        log_success "Git hooks setup completed"
    else
        log_info "Not a Git repository, skipping Git hooks setup"
    fi
}

# Create helpful development scripts
create_dev_scripts() {
    log_info "Creating development helper scripts..."
    
    # Start development servers script
    cat > scripts/start-dev.sh << 'EOF'
#!/bin/bash

echo "Starting development servers..."

# Start infrastructure
docker-compose up -d zookeeper kafka redis postgres

# Start backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Start frontend
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "Development servers started:"
echo "  Backend: http://localhost:8000"
echo "  Frontend: http://localhost:3000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap "kill $BACKEND_PID $FRONTEND_PID; docker-compose down; exit" INT
wait
EOF
    
    chmod +x scripts/start-dev.sh
    
    # Stop development servers script
    cat > scripts/stop-dev.sh << 'EOF'
#!/bin/bash

echo "Stopping development servers..."

# Kill any running uvicorn processes
pkill -f "uvicorn app.main:app" || true

# Kill any running Next.js processes
pkill -f "next dev" || true

# Stop Docker services
docker-compose down

echo "Development servers stopped"
EOF
    
    chmod +x scripts/stop-dev.sh
    
    # Reset development environment script
    cat > scripts/reset-dev.sh << 'EOF'
#!/bin/bash

echo "Resetting development environment..."

# Stop all services
./scripts/stop-dev.sh

# Remove Docker containers and volumes
docker-compose down -v
docker system prune -f

# Remove node_modules and reinstall
rm -rf frontend/node_modules
cd frontend && npm install && cd ..

# Remove Python virtual environment and recreate
rm -rf backend/venv
cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && cd ..

echo "Development environment reset completed"
EOF
    
    chmod +x scripts/reset-dev.sh
    
    log_success "Development helper scripts created"
}

# Main setup function
main() {
    log_info "Setting up development environment for Business Systems Integration Platform"
    
    check_prerequisites
    setup_environment
    create_dockerfiles
    setup_backend
    setup_frontend
    setup_docker
    start_infrastructure
    setup_database
    setup_git_hooks
    create_dev_scripts
    
    log_success "Development environment setup completed!"
    
    echo ""
    log_info "Next steps:"
    log_info "1. Update .env file with your API keys and configuration"
    log_info "2. Start development servers: ./scripts/start-dev.sh"
    log_info "3. Visit http://localhost:3000 for the frontend"
    log_info "4. Visit http://localhost:8000/docs for API documentation"
    echo ""
    log_info "Useful commands:"
    log_info "  ./scripts/start-dev.sh  - Start all development servers"
    log_info "  ./scripts/stop-dev.sh   - Stop all development servers"
    log_info "  ./scripts/reset-dev.sh  - Reset development environment"
    log_info "  ./scripts/deploy.sh     - Deploy the application"
    log_info "  ./scripts/backup.sh     - Backup application data"
}

# Run main function
main