#!/bin/bash

# Business Systems Integration Platform - Backup Script
# Usage: ./backup.sh [full|incremental] [retention_days]

set -e

# Configuration
BACKUP_TYPE=${1:-full}
RETENTION_DAYS=${2:-30}
BACKUP_BASE_DIR="./backups"
PROJECT_NAME="business-systems-platform"
S3_BUCKET="your-backup-bucket"  # Replace with your S3 bucket

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

# Create backup directory structure
setup_backup_structure() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    BACKUP_DIR="${BACKUP_BASE_DIR}/${BACKUP_TYPE}_${timestamp}"
    
    mkdir -p "$BACKUP_DIR"/{database,redis,files,config,logs}
    
    log_info "Backup directory created: $BACKUP_DIR"
}

# Backup PostgreSQL database
backup_database() {
    log_info "Backing up PostgreSQL database..."
    
    local db_backup_file="$BACKUP_DIR/database/postgres_backup.sql"
    
    # Create database dump
    docker-compose exec postgres pg_dumpall -U admin > "$db_backup_file"
    
    # Compress the backup
    gzip "$db_backup_file"
    
    local size=$(du -h "$db_backup_file.gz" | cut -f1)
    log_success "Database backup completed: $db_backup_file.gz ($size)"
}

# Backup Redis data
backup_redis() {
    log_info "Backing up Redis data..."
    
    local redis_backup_dir="$BACKUP_DIR/redis"
    
    # Trigger Redis save
    docker-compose exec redis redis-cli BGSAVE
    
    # Wait for save to complete
    while [ "$(docker-compose exec redis redis-cli LASTSAVE)" = "$(docker-compose exec redis redis-cli LASTSAVE)" ]; do
        sleep 1
    done
    
    # Copy Redis dump file
    docker cp $(docker-compose ps -q redis):/data/dump.rdb "$redis_backup_dir/"
    
    # Compress the backup
    gzip "$redis_backup_dir/dump.rdb"
    
    local size=$(du -h "$redis_backup_dir/dump.rdb.gz" | cut -f1)
    log_success "Redis backup completed: $redis_backup_dir/dump.rdb.gz ($size)"
}

# Backup application files
backup_application_files() {
    log_info "Backing up application files..."
    
    local files_backup_dir="$BACKUP_DIR/files"
    
    # Backup uploaded files (if any)
    if [ -d "./uploads" ]; then
        cp -r ./uploads "$files_backup_dir/"
        log_info "Uploaded files backed up"
    fi
    
    # Backup logs
    if [ -d "./logs" ]; then
        cp -r ./logs "$BACKUP_DIR/logs/"
        log_info "Log files backed up"
    fi
    
    # Backup any persistent volumes
    for volume in $(docker volume ls -q | grep "$PROJECT_NAME"); do
        log_info "Backing up volume: $volume"
        docker run --rm \
            -v "$volume":/source:ro \
            -v "$(pwd)/$files_backup_dir":/backup \
            alpine tar czf "/backup/${volume}.tar.gz" -C /source .
    done
    
    log_success "Application files backup completed"
}

# Backup configuration files
backup_configuration() {
    log_info "Backing up configuration files..."
    
    local config_backup_dir="$BACKUP_DIR/config"
    
    # Backup environment files
    cp .env* "$config_backup_dir/" 2>/dev/null || log_warning "No .env files found"
    
    # Backup Docker Compose files
    cp docker-compose*.yml "$config_backup_dir/"
    
    # Backup any configuration directories
    if [ -d "./config" ]; then
        cp -r ./config "$config_backup_dir/"
    fi
    
    # Backup scripts
    if [ -d "./scripts" ]; then
        cp -r ./scripts "$config_backup_dir/"
    fi
    
    log_success "Configuration backup completed"
}

# Create backup manifest
create_manifest() {
    log_info "Creating backup manifest..."
    
    local manifest_file="$BACKUP_DIR/backup_manifest.json"
    
    cat > "$manifest_file" << EOF
{
  "backup_type": "$BACKUP_TYPE",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "environment": "${ENVIRONMENT:-unknown}",
  "version": "${VERSION:-unknown}",
  "services": {
    "postgres": {
      "included": true,
      "file": "database/postgres_backup.sql.gz"
    },
    "redis": {
      "included": true,
      "file": "redis/dump.rdb.gz"
    },
    "application_files": {
      "included": true,
      "directory": "files/"
    },
    "configuration": {
      "included": true,
      "directory": "config/"
    }
  },
  "total_size": "$(du -sh "$BACKUP_DIR" | cut -f1)",
  "file_count": $(find "$BACKUP_DIR" -type f | wc -l)
}
EOF
    
    log_success "Backup manifest created: $manifest_file"
}

# Upload to remote storage
upload_to_remote() {
    if command -v aws &> /dev/null && [ -n "$S3_BUCKET" ]; then
        log_info "Uploading backup to S3..."
        
        # Create compressed archive of entire backup
        local archive_name="$(basename "$BACKUP_DIR").tar.gz"
        tar -czf "$BACKUP_BASE_DIR/$archive_name" -C "$BACKUP_BASE_DIR" "$(basename "$BACKUP_DIR")"
        
        # Upload to S3
        aws s3 cp "$BACKUP_BASE_DIR/$archive_name" "s3://$S3_BUCKET/backups/"
        
        # Clean up local archive
        rm "$BACKUP_BASE_DIR/$archive_name"
        
        log_success "Backup uploaded to S3: s3://$S3_BUCKET/backups/$archive_name"
    else
        log_warning "AWS CLI not configured or S3_BUCKET not set. Skipping remote upload."
    fi
}

# Cleanup old backups
cleanup_old_backups() {
    log_info "Cleaning up backups older than $RETENTION_DAYS days..."
    
    # Find and remove old backup directories
    find "$BACKUP_BASE_DIR" -type d -name "*_*" -mtime +$RETENTION_DAYS -exec rm -rf {} \; 2>/dev/null || true
    
    # Cleanup remote backups if AWS is configured
    if command -v aws &> /dev/null && [ -n "$S3_BUCKET" ]; then
        # Note: This would require more sophisticated S3 lifecycle management
        log_info "Note: Configure S3 lifecycle policies for automatic cleanup of old backups"
    fi
    
    log_success "Old backups cleaned up"
}

# Verify backup integrity
verify_backup() {
    log_info "Verifying backup integrity..."
    
    local errors=0
    
    # Check if all expected files exist
    if [ ! -f "$BACKUP_DIR/database/postgres_backup.sql.gz" ]; then
        log_error "Database backup file missing"
        ((errors++))
    fi
    
    if [ ! -f "$BACKUP_DIR/redis/dump.rdb.gz" ]; then
        log_error "Redis backup file missing"
        ((errors++))
    fi
    
    if [ ! -f "$BACKUP_DIR/backup_manifest.json" ]; then
        log_error "Backup manifest missing"
        ((errors++))
    fi
    
    # Test compressed files
    if ! gzip -t "$BACKUP_DIR/database/postgres_backup.sql.gz" 2>/dev/null; then
        log_error "Database backup file is corrupted"
        ((errors++))
    fi
    
    if ! gzip -t "$BACKUP_DIR/redis/dump.rdb.gz" 2>/dev/null; then
        log_error "Redis backup file is corrupted"
        ((errors++))
    fi
    
    if [ $errors -eq 0 ]; then
        log_success "Backup integrity verification passed"
        return 0
    else
        log_error "Backup integrity verification failed with $errors errors"
        return 1
    fi
}

# Send notification
send_notification() {
    local status=$1
    local message=$2
    
    # Email notification (if configured)
    if command -v mail &> /dev/null && [ -n "$NOTIFICATION_EMAIL" ]; then
        echo "$message" | mail -s "Backup $status - $PROJECT_NAME" "$NOTIFICATION_EMAIL"
    fi
    
    # Slack notification (if webhook configured)
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"Backup $status: $message\"}" \
            "$SLACK_WEBHOOK_URL" 2>/dev/null || true
    fi
}

# Main backup function
main() {
    log_info "Starting $BACKUP_TYPE backup..."
    
    # Check if services are running
    if ! docker-compose ps | grep -q "Up"; then
        log_error "Services are not running. Start services first with: docker-compose up -d"
        exit 1
    fi
    
    setup_backup_structure
    
    # Perform backup operations
    backup_database
    backup_redis
    backup_application_files
    backup_configuration
    create_manifest
    
    # Verify backup
    if verify_backup; then
        upload_to_remote
        cleanup_old_backups
        
        local backup_size=$(du -sh "$BACKUP_DIR" | cut -f1)
        local message="Backup completed successfully. Size: $backup_size, Location: $BACKUP_DIR"
        log_success "$message"
        send_notification "SUCCESS" "$message"
    else
        local message="Backup completed with errors. Please check the backup manually."
        log_error "$message"
        send_notification "FAILED" "$message"
        exit 1
    fi
}

# Show usage
show_usage() {
    echo "Usage: $0 [backup_type] [retention_days]"
    echo ""
    echo "Backup Types:"
    echo "  full         - Complete backup of all data (default)"
    echo "  incremental  - Incremental backup (not implemented yet)"
    echo ""
    echo "Retention:"
    echo "  retention_days - Number of days to keep backups (default: 30)"
    echo ""
    echo "Environment Variables:"
    echo "  S3_BUCKET           - S3 bucket for remote backup storage"
    echo "  NOTIFICATION_EMAIL  - Email for backup notifications"
    echo "  SLACK_WEBHOOK_URL   - Slack webhook for notifications"
    echo ""
    echo "Examples:"
    echo "  $0                  # Full backup with 30-day retention"
    echo "  $0 full 7           # Full backup with 7-day retention"
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
        if [[ "$1" =~ ^(full|incremental)$ ]]; then
            main
        else
            log_error "Invalid backup type: $1"
            show_usage
            exit 1
        fi
        ;;
esac