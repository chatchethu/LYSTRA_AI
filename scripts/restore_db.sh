#!/bin/bash
# scripts/restore_db.sh

BACKUP_FILE="$1"

if [ -z "$BACKUP_FILE" ]; then
  echo "Usage: $0 <path_to_backup_file>"
  exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
  echo "Error: Backup file $BACKUP_FILE not found!"
  exit 1
fi

echo "Restoring database from $BACKUP_FILE..."
cat "$BACKUP_FILE" | docker exec -i personalai_postgres psql -U personalai -d personalai

if [ $? -eq 0 ]; then
    echo "Database restore completed successfully."
else
    echo "Error: Database restore failed!"
    exit 1
fi
