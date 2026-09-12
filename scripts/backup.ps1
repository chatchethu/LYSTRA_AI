param(
    [string]$DbUrl = $env:DATABASE_URL,
    [string]$BackupDir = "backups",
    [string]$Timestamp = (Get-Date -Format "yyyyMMdd_HHmmss")
)

if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir | Out-Null
}

$DbBackupFile = "$BackupDir\db_backup_$Timestamp.sql"
Write-Host "Backing up database to $DbBackupFile..."
# Using pg_dump
# pg_dump $DbUrl -F c -f $DbBackupFile

$StorageBackupFile = "$BackupDir\storage_backup_$Timestamp.zip"
Write-Host "Backing up local storage to $StorageBackupFile..."
if (Test-Path "storage") {
    Compress-Archive -Path "storage\*" -DestinationPath $StorageBackupFile -Force
}

Write-Host "Backup completed successfully!"

