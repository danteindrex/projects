# Troubleshooting Guide

## Common Issues and Solutions

### Application Startup Issues

#### Issue: Services fail to start

**Symptoms:**
- Docker containers exit immediately
- "Connection refused" errors
- Services show "Restarting" status

**Diagnosis:**
```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres

# Check resource usage
docker stats
```

**Solutions:**

1. **Port conflicts:**
```bash
# Check what's using the ports
sudo netstat -tulpn | grep :8000
sudo netstat -tulpn | grep :3000
sudo netstat -tulpn | grep :5432

# Kill conflicting processes
sudo kill -9 <PID>

# Or change ports in docker-compose.yml
```

2. **Insufficient resources:**
```bash
# Check available memory and disk
free -h
df -h

# Increase Docker memory limits
# Docker Desktop: Settings > Resources > Memory
```

3. **Missing environment variables:**
```bash
# Verify .env file exists and has required variables
cat .env | grep -E "(DATABASE_URL|SECRET_KEY|OPENAI_API_KEY)"

# Copy from example if missing
cp .env.example .env
```

#### Issue: Database connection errors

**Symptoms:**
- "Could not connect to PostgreSQL"
- "Connection timeout"
- Backend health check fails

**Diagnosis:**
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Test database connection
docker-compose exec postgres pg_isready -U admin

# Check database logs
docker-compose logs postgres
```

**Solutions:**

1. **PostgreSQL not ready:**
```bash
# Wait for PostgreSQL to fully start
sleep 30

# Restart PostgreSQL container
docker-compose restart postgres
```

2. **Wrong credentials:**
```bash
# Verify database credentials in .env
grep DATABASE_URL .env

# Reset to default development values
DATABASE_URL=postgresql://admin:password123@postgres:5432/business_platform
```

3. **Database doesn't exist:**
```bash
# Create database manually
docker-compose exec postgres createdb -U admin business_platform
```

### Frontend Issues

#### Issue: Frontend won't load

**Symptoms:**
- Blank page or loading spinner
- "Cannot connect to server" errors
- 502/503 errors

**Diagnosis:**
```bash
# Check frontend container
docker-compose logs frontend

# Test frontend port
curl http://localhost:3000

# Check if frontend process is running
docker-compose exec frontend ps aux | grep node
```

**Solutions:**

1. **Build errors:**
```bash
# Check for build errors
docker-compose logs frontend | grep ERROR

# Rebuild frontend
cd frontend
npm install
npm run build
```

2. **API connection issues:**
```bash
# Verify API URL in frontend config
grep -r "localhost:8000" frontend/src/

# Test API connectivity
curl http://localhost:8000/health
```

3. **Node.js memory issues:**
```bash
# Increase Node.js memory limit
export NODE_OPTIONS="--max-old-space-size=4096"
npm run dev
```

#### Issue: Chat interface not working

**Symptoms:**
- Messages don't send
- WebSocket connection fails
- No AI responses

**Diagnosis:**
```bash
# Check WebSocket connection in browser console
# Open Developer Tools > Console

# Test WebSocket endpoint
wscat -c ws://localhost:8000/api/v1/chat/ws/test_session

# Check backend WebSocket logs
docker-compose logs backend | grep websocket
```

**Solutions:**

1. **WebSocket connection blocked:**
```bash
# Check if reverse proxy blocks WebSocket
# Update nginx/apache config to support WebSocket upgrade

# Test direct backend connection
wscat -c ws://localhost:8000/api/v1/chat/ws/test
```

2. **Authentication issues:**
```bash
# Verify JWT token is valid
# Check browser localStorage/sessionStorage

# Test authentication endpoint
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/v1/auth/me
```

### Backend API Issues

#### Issue: API returns 500 errors

**Symptoms:**
- Internal server errors
- Unhandled exceptions
- Services crash

**Diagnosis:**
```bash
# Check backend logs for stack traces
docker-compose logs backend | grep -A 10 ERROR

# Check application metrics
curl http://localhost:8000/health

# Monitor resource usage
docker stats backend
```

**Solutions:**

1. **Unhandled exceptions:**
```bash
# Check Python dependencies
docker-compose exec backend pip list

# Update dependencies
docker-compose exec backend pip install -r requirements.txt --upgrade
```

2. **Memory leaks:**
```bash
# Restart backend service
docker-compose restart backend

# Monitor memory usage over time
watch docker stats backend
```

3. **Database connection pool exhausted:**
```bash
# Check active connections
docker-compose exec postgres psql -U admin -c "SELECT count(*) FROM pg_stat_activity;"

# Increase connection pool size in DATABASE_URL
DATABASE_URL=postgresql://user:pass@host:5432/db?pool_size=20&max_overflow=30
```

#### Issue: Authentication problems

**Symptoms:**
- Login fails with correct credentials
- JWT tokens expire immediately
- Permission denied errors

**Diagnosis:**
```bash
# Test login endpoint
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=testpassword"

# Check token generation
docker-compose exec backend python -c "
from app.core.security import create_access_token
print(create_access_token({'sub': 'test'}))"
```

**Solutions:**

1. **Secret key issues:**
```bash
# Generate new secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update SECRET_KEY in .env
SECRET_KEY=your_new_secret_key_here
```

2. **Clock synchronization:**
```bash
# Check system time
date

# Sync system clock
sudo ntpdate -s time.nist.gov
```

### Performance Issues

#### Issue: Slow response times

**Symptoms:**
- API calls take >5 seconds
- Frontend loads slowly
- Chat responses are delayed

**Diagnosis:**
```bash
# Check response times
curl -w "%{time_total}\n" -o /dev/null -s http://localhost:8000/health

# Monitor system resources
htop

# Check database performance
docker-compose exec postgres psql -U admin -c "
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;"
```

**Solutions:**

1. **Database optimization:**
```sql
-- Add missing indexes
CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_integrations_user_id ON integrations(user_id);

-- Analyze slow queries
EXPLAIN ANALYZE SELECT * FROM chat_messages WHERE session_id = 'uuid';
```

2. **Application optimization:**
```bash
# Enable connection pooling
# Add caching layer
# Optimize API endpoints

# Check for memory leaks
valgrind --tool=memcheck python app/main.py
```

3. **Infrastructure scaling:**
```bash
# Increase container resources
docker-compose up --scale backend=3

# Add load balancer
# Use Redis for caching
```

#### Issue: High memory usage

**Symptoms:**
- Containers using >2GB RAM
- System becomes unresponsive
- Out of memory errors

**Diagnosis:**
```bash
# Check memory usage by container
docker stats --no-stream

# Check memory leaks
docker-compose exec backend python -c "
import gc
import psutil
print(f'Memory: {psutil.virtual_memory().percent}%')
print(f'Objects: {len(gc.get_objects())}')
"
```

**Solutions:**

1. **Container memory limits:**
```yaml
# docker-compose.yml
services:
  backend:
    mem_limit: 1g
    memswap_limit: 1g
```

2. **Application optimization:**
```python
# Close database connections properly
# Limit concurrent operations
# Use pagination for large datasets
```

### Integration Issues

#### Issue: External API connections fail

**Symptoms:**
- Integration tests fail
- "Connection timeout" errors
- External services unreachable

**Diagnosis:**
```bash
# Test network connectivity
curl -v https://api.external-service.com/health

# Check DNS resolution
nslookup api.external-service.com

# Test from container
docker-compose exec backend curl https://api.external-service.com
```

**Solutions:**

1. **Network configuration:**
```bash
# Check Docker network
docker network ls
docker network inspect projects_default

# Allow outbound connections
sudo ufw allow out 443
sudo ufw allow out 80
```

2. **Proxy configuration:**
```bash
# Configure proxy if needed
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080
```

3. **API credentials:**
```bash
# Verify API keys
echo $OPENAI_API_KEY | head -c 20

# Test API key validity
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models
```

### WebSocket Issues

#### Issue: WebSocket connections drop

**Symptoms:**
- Chat disconnects frequently
- "WebSocket closed" errors
- Connection timeouts

**Diagnosis:**
```bash
# Check WebSocket logs
docker-compose logs backend | grep -i websocket

# Test WebSocket stability
wscat -c ws://localhost:8000/api/v1/chat/ws/test

# Monitor network traffic
sudo netstat -an | grep :8000
```

**Solutions:**

1. **Connection timeouts:**
```python
# Increase WebSocket timeout in backend
# app/api/api_v1/endpoints/chat.py
websocket.timeout = 300  # 5 minutes
```

2. **Load balancer configuration:**
```nginx
# nginx.conf
location /api/v1/chat/ws/ {
    proxy_pass http://backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 300s;
    proxy_send_timeout 300s;
}
```

3. **Client-side reconnection:**
```javascript
// Implement auto-reconnect in frontend
const reconnectWebSocket = () => {
  setTimeout(() => {
    connectWebSocket();
  }, 5000);
};
```

### Kafka Issues

#### Issue: Kafka not receiving messages

**Symptoms:**
- Log streams not updating
- Messages not appearing in Kafka UI
- Producer/consumer errors

**Diagnosis:**
```bash
# Check Kafka status
docker-compose logs kafka

# List topics
docker-compose exec kafka kafka-topics.sh \
  --list --bootstrap-server localhost:9092

# Check consumer groups
docker-compose exec kafka kafka-consumer-groups.sh \
  --list --bootstrap-server localhost:9092
```

**Solutions:**

1. **Kafka connectivity:**
```bash
# Test Kafka connection
docker-compose exec kafka kafka-console-producer.sh \
  --topic test --bootstrap-server localhost:9092

# Restart Kafka services
docker-compose restart zookeeper kafka
```

2. **Topic configuration:**
```bash
# Create topics manually
docker-compose exec kafka kafka-topics.sh \
  --create --topic business_platform.chat \
  --bootstrap-server localhost:9092 \
  --partitions 3 --replication-factor 1
```

### Docker Issues

#### Issue: Docker containers won't start

**Symptoms:**
- "No such file or directory" errors
- Permission denied errors
- Container exits with code 125

**Diagnosis:**
```bash
# Check Docker daemon
sudo systemctl status docker

# Check Docker logs
sudo journalctl -u docker.service

# Verify Docker Compose file
docker-compose config
```

**Solutions:**

1. **Docker daemon issues:**
```bash
# Restart Docker
sudo systemctl restart docker

# Check Docker disk usage
docker system df

# Clean up Docker resources
docker system prune -a
```

2. **File permissions:**
```bash
# Fix ownership
sudo chown -R $USER:$USER .

# Fix execute permissions
chmod +x scripts/*.sh
```

## Performance Optimization

### Database Optimization

```sql
-- Add indexes for common queries
CREATE INDEX CONCURRENTLY idx_chat_messages_created_at ON chat_messages(created_at);
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);

-- Analyze table statistics
ANALYZE chat_messages;
ANALYZE users;

-- Check for unused indexes
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE schemaname = 'public';
```

### Application Optimization

```python
# Use connection pooling
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True
)

# Implement caching
from functools import lru_cache

@lru_cache(maxsize=128)
def get_integration_config(integration_id: str):
    # Expensive operation
    pass
```

### Frontend Optimization

```javascript
// Code splitting
const ChatInterface = lazy(() => import('./components/chat/ChatInterface'));

// Memoization
const MemoizedComponent = React.memo(({ data }) => {
  return <ExpensiveComponent data={data} />;
});

// Virtual scrolling for large lists
import { FixedSizeList as List } from 'react-window';
```

## Monitoring and Alerting

### Health Checks

```bash
#!/bin/bash
# health-check.sh

# Check all services
services=("backend" "frontend" "postgres" "redis" "kafka")

for service in "${services[@]}"; do
    if ! docker-compose ps $service | grep -q "Up"; then
        echo "ALERT: $service is down"
        # Send notification
    fi
done

# Check API endpoints
if ! curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "ALERT: Backend API is down"
fi

if ! curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "ALERT: Frontend is down"
fi
```

### Log Analysis

```bash
# Analyze error patterns
docker-compose logs backend | grep ERROR | sort | uniq -c | sort -nr

# Monitor response times
docker-compose logs backend | grep "Process-Time" | awk '{print $NF}' | sort -n

# Check memory usage trends
docker stats --no-stream | awk '{print $4}' | grep -v "MEM"
```

## Recovery Procedures

### Disaster Recovery

```bash
#!/bin/bash
# disaster-recovery.sh

# Stop all services
docker-compose down

# Restore from backup
./scripts/restore.sh latest

# Start services
docker-compose up -d

# Verify system health
sleep 30
./scripts/health-check.sh
```

### Data Recovery

```bash
# Restore specific database
./scripts/restore-db.sh backup_20231201_020000

# Restore Redis data
docker cp backup/redis_dump.rdb $(docker-compose ps -q redis):/data/
docker-compose restart redis

# Restore uploaded files
tar -xzf backup/files.tar.gz -C ./uploads/
```

## Getting Help

### Debug Information Collection

```bash
#!/bin/bash
# collect-debug-info.sh

echo "=== System Information ===" > debug-info.txt
uname -a >> debug-info.txt
docker --version >> debug-info.txt
docker-compose --version >> debug-info.txt

echo "=== Container Status ===" >> debug-info.txt
docker-compose ps >> debug-info.txt

echo "=== Resource Usage ===" >> debug-info.txt
docker stats --no-stream >> debug-info.txt

echo "=== Recent Logs ===" >> debug-info.txt
docker-compose logs --tail=100 >> debug-info.txt

echo "Debug information collected in debug-info.txt"
```

### Support Channels

1. **GitHub Issues**: Create an issue with debug information
2. **Documentation**: Check docs/ directory for detailed guides
3. **Community**: Join our Discord/Slack for community support
4. **Enterprise Support**: Contact support@yourcompany.com for enterprise users

### Useful Commands Reference

```bash
# Quick diagnostics
docker-compose ps                          # Check service status
docker-compose logs -f backend            # Follow backend logs
docker stats                              # Resource usage
curl http://localhost:8000/health         # Test backend health

# Restart services
docker-compose restart backend            # Restart single service
docker-compose down && docker-compose up -d  # Full restart

# Clean up
docker system prune -f                    # Clean unused Docker resources
docker-compose down -v                    # Remove containers and volumes

# Database operations
docker-compose exec postgres psql -U admin -d business_platform  # Connect to DB
./scripts/backup.sh                       # Create backup
./scripts/deploy.sh development           # Deploy to development
```