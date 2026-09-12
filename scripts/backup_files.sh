#!/bin/bash
# scripts/backup_files.sh

UPLOADS_DIR="${1:-./uploads}"
BACKUP_DIR="${2:-./backups/files}"

if [ ! -d "$UPLOADS_DIR" ]; then
  echo "Warning: Uploads directory $UPLOADS_DIR does not exist. Creating empty directory..."
  mkdir -p "$UPLOADS_DIR"
fi

mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/files_backup_$TIMESTAMP.tar.gz"

echo "Backing up files from $UPLOADS_DIR to $BACKUP_FILE..."
tar -czf "$BACKUP_FILE" -C "$UPLOADS_DIR" .

if [ $? -eq 0 ]; then
    echo "Files backup completed successfully: $BACKUP_FILE"
else
    echo "Error: Files backup failed!"
    exit 1
fi
