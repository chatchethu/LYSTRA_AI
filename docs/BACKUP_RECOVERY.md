# Backup and Recovery Strategy

This document outlines the strategy for backing up and restoring the NOVA AI system data, specifically focusing on the PostgreSQL database and the user file uploads.

## Backup Components

1.  **Database Backups**: The relational database (PostgreSQL) holds all structured data, including application state, user configurations, and metadata.
2.  **File Backups**: The local filesystem (specifically the `uploads/` directory) holds unstructured data uploaded or processed by the system.

## Automation Scripts

Located in the `scripts/` directory:

*   `backup_db.sh`: Creates a standard SQL dump of the PostgreSQL database.
*   `restore_db.sh`: Restores a database dump to the PostgreSQL instance.
*   `backup_files.sh`: Creates a tar.gz archive of the `uploads/` directory.
*   `restore_files.sh`: Restores a file archive to the `uploads/` directory.

## Retention Strategy

To manage disk space while ensuring sufficient recovery points, implement the following retention schedule for automated backups (e.g., via cron):

*   **Daily Backups**: Retain daily backups for 7 days.
*   **Weekly Backups**: Retain weekly backups (taken on Sundays) for 4 weeks.
*   **Monthly Backups**: Retain monthly backups (taken on the 1st of the month) for 6 months.
*   *Pruning*: A scheduled cleanup task (cron job) should automatically delete backups older than the retention threshold for each category.

## Storage and Security

*   **Location**: Backups are stored in `backups/db/` and `backups/files/` by default. It is recommended to sync these local backup directories to an external object storage solution (e.g., AWS S3, Azure Blob Storage) using a tool like `rclone` or the AWS CLI.
*   **Encryption**: Off-site backups should be encrypted at rest. It is recommended to compress and encrypt backups via GPG or a similar tool before offloading.

## Recovery Procedures

### 1. Database Restoration

In case of database corruption or data loss:

1.  Locate the most recent healthy backup file (`.sql`).
2.  Run the restore script:
    ```bash
    ./scripts/restore_db.sh ./backups/db/db_backup_YYYYMMDD_HHMMSS.sql
    ```
    *Warning*: This will overwrite the current state of the database with the state at the time of the backup.

### 2. Files Restoration

In case of missing or corrupted uploaded files:

1.  Locate the most recent files backup (`.tar.gz`).
2.  Run the restore script:
    ```bash
    ./scripts/restore_files.sh ./backups/files/files_backup_YYYYMMDD_HHMMSS.tar.gz
    ```

### Disaster Recovery

For complete environment failure:
1. Re-deploy the infrastructure (e.g., `docker-compose up -d`).
2. Wait for services to become healthy.
3. Perform database restoration using `restore_db.sh`.
4. Perform files restoration using `restore_files.sh`.
5. Run integration tests to verify data integrity.

## Migration Strategy

When moving to a new server or environment:
1. Ensure the new environment has the requisite versions of Docker, PostgreSQL, etc.
2. Halt the application on the old server (keeping DB running for a final backup if needed).
3. Take a final complete backup of the database and files.
4. Transfer the backup artifacts to the new server.
5. Spin up the infrastructure on the new server.
6. Perform the DB and File restorations.
7. Start the application services and verify system health.
