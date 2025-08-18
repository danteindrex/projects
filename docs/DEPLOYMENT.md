# Deployment Guide

## Overview

This guide covers deploying the Business Systems Integration Platform to various environments including development, staging, and production.

## Prerequisites

### System Requirements

- **CPU**: 2+ cores (4+ recommended for production)
- **RAM**: 4GB minimum (8GB+ recommended for production)
- **Storage**: 20GB minimum (SSD recommended)
- **OS**: Linux (Ubuntu 20.04+, RHEL 8+, or similar)

### Required Software

- Docker 20.10+
- Docker Compose 2.0+
- Git
- SSL certificates (for production)

### External Services

- **Supabase** account for authentication and database
- **OpenAI** or **Anthropic** API keys for AI functionality
- **Kafka** cluster (optional for production scale)
- **Redis** cluster (optional for production scale)

## Quick Start

### 1. Clone Repository

```bash
git clone <repository-url>
cd business-systems-platform
```

### 2. Environment Setup

```bash
# Development
./scripts/setup-dev.sh

# Production
cp .env.example .env.production
# Edit .env.production with production values
```

### 3. Deploy

```bash
# Development
./scripts/deploy.sh development

# Production  
./scripts/deploy.sh production v1.0.0
```

## Environment Configuration

### Development Environment

Create `.env.development`:

```bash
# Database
DATABASE_URL=postgresql://admin:password123@localhost:5432/business_platform

# Redis
REDIS_URL=redis://localhost:6379

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_PREFIX=business_platform_dev

# Security
SECRET_KEY=dev_secret_key_change_in_production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API
API_V1_STR=/api/v1
CORS_ORIGINS=["http://localhost:3000"]
ALLOWED_HOSTS=["localhost", "127.0.0.1"]

# Development
DEBUG=true
ENVIRONMENT=development
LOG_LEVEL=DEBUG

# External APIs
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
```

### Production Environment

Create `.env.production`:

```bash
# Database (use managed PostgreSQL service)
DATABASE_URL=postgresql://user:password@db-host:5432/business_platform

# Redis (use managed Redis service)
REDIS_URL=redis://redis-host:6379

# Kafka (use managed Kafka service)
KAFKA_BOOTSTRAP_SERVERS=kafka-host:9092
KAFKA_TOPIC_PREFIX=business_platform_prod

# Security (IMPORTANT: Use strong values)
SECRET_KEY=your_very_long_secure_secret_key_here
MASTER_ENCRYPTION_KEY=your_encryption_key_base64_encoded
ACCESS_TOKEN_EXPIRE_MINUTES=15

# API
API_V1_STR=/api/v1
CORS_ORIGINS=["https://yourdomain.com"]
ALLOWED_HOSTS=["yourdomain.com", "api.yourdomain.com"]

# Production
DEBUG=false
ENVIRONMENT=production
LOG_LEVEL=INFO

# Rate limiting
RATE_LIMIT_PER_MINUTE=30

# External APIs
OPENAI_API_KEY=your_production_openai_key
ANTHROPIC_API_KEY=your_production_anthropic_key

# Monitoring
SENTRY_DSN=your_sentry_dsn
```

## Deployment Strategies

### 1. Development Deployment

For local development and testing:

```bash
# Start infrastructure services
docker-compose up -d zookeeper kafka redis postgres

# Start application in development mode
cd backend && source venv/bin/activate && uvicorn app.main:app --reload &
cd frontend && npm run dev &
```

### 2. Docker Deployment

For containerized deployment:

```bash
# Build images
docker-compose build

# Deploy all services
docker-compose up -d

# Check status
docker-compose ps
```

### 3. Production Deployment

For production environments:

```bash
# Deploy with production configuration
./scripts/deploy.sh production v1.0.0

# Verify deployment
curl -f http://localhost:8000/health
curl -f http://localhost:3000
```

## Cloud Platform Deployment

### AWS Deployment

#### Using EC2 + ECS

1. **Setup Infrastructure**:
```bash
# Create VPC, subnets, security groups
# Launch EC2 instances or ECS cluster
# Setup RDS PostgreSQL, ElastiCache Redis, MSK Kafka
```

2. **Deploy Application**:
```bash
# Build and push images to ECR
docker build -t your-account.dkr.ecr.region.amazonaws.com/platform-backend .
docker push your-account.dkr.ecr.region.amazonaws.com/platform-backend

# Deploy ECS services
aws ecs update-service --cluster platform-cluster --service backend-service
```

3. **Configuration**:
```bash
# Use AWS Systems Manager Parameter Store or Secrets Manager
AWS_REGION=us-east-1
DATABASE_URL=postgresql://user:pass@rds-endpoint:5432/db
REDIS_URL=redis://elasticache-endpoint:6379
KAFKA_BOOTSTRAP_SERVERS=kafka-endpoint:9092
```

#### Using EKS (Kubernetes)

1. **Create Kubernetes manifests** (examples in `k8s/` directory):

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: your-registry/platform-backend:v1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: platform-secrets
              key: database-url
```

2. **Deploy**:
```bash
kubectl apply -f k8s/
kubectl get pods
```

### Google Cloud Platform

#### Using Cloud Run

1. **Deploy services**:
```bash
# Backend
gcloud run deploy backend \
  --image gcr.io/project-id/platform-backend \
  --platform managed \
  --region us-central1 \
  --set-env-vars DATABASE_URL=$DATABASE_URL

# Frontend  
gcloud run deploy frontend \
  --image gcr.io/project-id/platform-frontend \
  --platform managed \
  --region us-central1
```

2. **Setup managed services**:
- Cloud SQL for PostgreSQL
- Cloud Memorystore for Redis
- Cloud Pub/Sub (instead of Kafka)

### Azure Deployment

#### Using Container Instances

```bash
# Create resource group
az group create --name platform-rg --location eastus

# Deploy containers
az container create \
  --resource-group platform-rg \
  --name backend \
  --image your-registry/platform-backend:v1.0.0 \
  --environment-variables DATABASE_URL=$DATABASE_URL
```

## SSL/TLS Configuration

### Using Let's Encrypt

1. **Install Certbot**:
```bash
sudo apt install certbot python3-certbot-nginx
```

2. **Generate certificates**:
```bash
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com
```

3. **Update nginx configuration**:
```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

server {
    listen 443 ssl;
    server_name api.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Load Balancing

### Using nginx

```nginx
upstream backend {
    server localhost:8000;
    server localhost:8001;
    server localhost:8002;
}

upstream frontend {
    server localhost:3000;
    server localhost:3001;
}

server {
    listen 80;
    server_name yourdomain.com;
    
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Using HAProxy

```
global
    daemon

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend web_frontend
    bind *:80
    bind *:443 ssl crt /path/to/cert.pem
    redirect scheme https if !{ ssl_fc }
    
    acl is_api path_beg /api/
    use_backend api_backend if is_api
    default_backend web_backend

backend api_backend
    balance roundrobin
    server api1 localhost:8000 check
    server api2 localhost:8001 check

backend web_backend
    balance roundrobin
    server web1 localhost:3000 check
    server web2 localhost:3001 check
```

## Database Migrations

### Manual Migration

```bash
# Connect to database container
docker-compose exec postgres psql -U admin -d business_platform

# Run SQL migrations
\i migrations/001_initial_schema.sql
\i migrations/002_add_integrations.sql
```

### Automated Migration

```bash
# Using Alembic (if configured)
docker-compose exec backend alembic upgrade head

# Rollback if needed
docker-compose exec backend alembic downgrade -1
```

## Monitoring and Logging

### Application Monitoring

1. **Health checks**:
```bash
# Check application health
curl http://localhost:8000/health
curl http://localhost:3000/_health
```

2. **Metrics collection**:
```bash
# Prometheus metrics endpoint
curl http://localhost:8000/metrics
```

### Log Management

1. **Centralized logging**:
```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

2. **Log aggregation**:
```bash
# Using ELK stack
docker-compose -f docker-compose.logging.yml up -d
```

## Backup and Recovery

### Automated Backups

```bash
# Schedule daily backups
echo "0 2 * * * /path/to/scripts/backup.sh full 30" | crontab -
```

### Manual Backup

```bash
# Create backup
./scripts/backup.sh full

# Restore from backup
./scripts/restore.sh backup_20231201_020000
```

## Security Considerations

### Production Security Checklist

- [ ] Use HTTPS everywhere
- [ ] Strong passwords and API keys
- [ ] Enable firewall rules
- [ ] Regular security updates
- [ ] Encrypted database connections
- [ ] Secure secret management
- [ ] Rate limiting enabled
- [ ] Security headers configured
- [ ] Input validation and sanitization
- [ ] Regular security audits

### Network Security

```bash
# Configure firewall
sudo ufw enable
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw deny 5432/tcp   # Block direct database access
```

## Troubleshooting

### Common Issues

1. **Services not starting**:
```bash
# Check logs
docker-compose logs backend
docker-compose logs frontend

# Check resource usage
docker stats
```

2. **Database connection issues**:
```bash
# Test database connection
docker-compose exec backend python -c "from app.db.database import engine; print(engine.execute('SELECT 1').scalar())"
```

3. **High memory usage**:
```bash
# Restart services
docker-compose restart

# Check for memory leaks
docker stats --no-stream
```

### Performance Optimization

1. **Database optimization**:
```sql
-- Add indexes
CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_integrations_user_id ON integrations(user_id);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM chat_messages WHERE session_id = 'uuid';
```

2. **Application optimization**:
```python
# Enable connection pooling
DATABASE_URL=postgresql://user:pass@host:5432/db?pool_size=20&max_overflow=30
```

3. **Frontend optimization**:
```javascript
// Enable compression
// Add CDN for static assets
// Optimize images and assets
```

## Rollback Procedures

### Quick Rollback

```bash
# Stop current deployment
docker-compose down

# Restore previous version
docker-compose -f docker-compose.yml -f docker-compose.v1.0.0.yml up -d

# Restore database from backup
./scripts/restore.sh backup_20231201_020000
```

### Blue-Green Deployment

```bash
# Deploy to green environment
./scripts/deploy.sh production v1.1.0 --target green

# Test green environment
curl http://green.yourdomain.com/health

# Switch traffic to green
./scripts/switch-traffic.sh green

# Keep blue as fallback
```

## Maintenance

### Regular Maintenance Tasks

```bash
# Weekly tasks
./scripts/backup.sh full 30
docker system prune -f
./scripts/update-dependencies.sh

# Monthly tasks  
./scripts/security-scan.sh
./scripts/performance-audit.sh
```

### Updates and Patches

```bash
# Update application
git pull origin main
./scripts/deploy.sh production v1.1.0

# Update dependencies
cd backend && pip install -r requirements.txt --upgrade
cd frontend && npm update
```