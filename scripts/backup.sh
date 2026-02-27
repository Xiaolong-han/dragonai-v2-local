#!/bin/bash
set -e

BACKUP_DIR="${BACKUP_DIR:-/backup/dragonai}"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=${RETENTION_DAYS:-7}

mkdir -p $BACKUP_DIR

echo "========================================"
echo "  DragonAI Backup Script"
echo "  Time: $(date)"
echo "========================================"

echo "[INFO] Backing up PostgreSQL..."
docker exec dragonai-postgres pg_dump -U ${DB_USER:-dragonai} ${DB_NAME:-dragonai} > $BACKUP_DIR/db_$DATE.sql
echo "[OK] Database backup: db_$DATE.sql"

echo "[INFO] Backing up ChromaDB..."
docker run --rm \
    -v dragonai-v2-local_backend_chroma:/source:ro \
    -v $BACKUP_DIR:/backup \
    alpine tar czf /backup/chroma_$DATE.tar.gz -C /source .
echo "[OK] ChromaDB backup: chroma_$DATE.tar.gz"

echo "[INFO] Backing up Storage..."
docker run --rm \
    -v dragonai-v2-local_backend_storage:/source:ro \
    -v $BACKUP_DIR:/backup \
    alpine tar czf /backup/storage_$DATE.tar.gz -C /source .
echo "[OK] Storage backup: storage_$DATE.tar.gz"

echo "[INFO] Cleaning old backups (older than $RETENTION_DAYS days)..."
find $BACKUP_DIR -name "*.sql" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete
echo "[OK] Cleanup completed"

echo "========================================"
echo "  Backup completed successfully!"
echo "  Location: $BACKUP_DIR"
echo "========================================"

ls -lh $BACKUP_DIR
