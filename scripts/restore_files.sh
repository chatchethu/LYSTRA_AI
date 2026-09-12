#!/bin/bash
# scripts/restore_files.sh

BACKUP_FILE="$1"
UPLOADS_DIR="${2:-./uploads}"

if [ -z "$BACKUP_FILE" ]; then
  echo "Usage: $0 <path_to_backup_file> [uploads_directory]"
  exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
  echo "Error: Backup file $BACKUP_FILE not found!"
  exit 1
fi

echo "Restoring files from $BACKUP_FILE to $UPLOADS_DIR..."
mkdir -p "$UPLOADS_DIR"
tar -xzf "$BACKUP_FILE" -C "$UPLOADS_DIR"

if [ $? -eq 0 ]; then
    echo "Files restore completed successfully."
else
    echo "Error: Files restore failed!"
    exit 1
fi
