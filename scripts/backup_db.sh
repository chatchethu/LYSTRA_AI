#!/bin/bash
# scripts/backup_db.sh

BACKUP_DIR="${1:-./backups/db}"
mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/db_backup_$TIMESTAMP.sql"

echo "Backing up database to $BACKUP_FILE..."
# Use pg_dump inside the container and pipe to the host file
docker exec -t personalai_postgres pg_dump -U personalai -d personalai -c > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "Database backup completed successfully: $BACKUP_FILE"
else
    echo "Error: Database backup failed!"
    exit 1
fi
