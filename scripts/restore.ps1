param(
    [string]$DbUrl = $env:DATABASE_URL,
    [string]$DbBackupFile,
    [string]$StorageBackupFile
)

if (-not $DbBackupFile) {
    Write-Error "Please provide a database backup file."
    exit 1
}

Write-Host "Restoring database from $DbBackupFile..."
# pg_restore -c -d $DbUrl $DbBackupFile

if ($StorageBackupFile) {
    Write-Host "Restoring storage from $StorageBackupFile..."
    if (Test-Path "storage") {
        Remove-Item -Recurse -Force "storage\*"
    } else {
        New-Item -ItemType Directory -Path "storage" | Out-Null
    }
    Expand-Archive -Path $StorageBackupFile -DestinationPath "storage" -Force
}

Write-Host "Restore completed successfully!"

