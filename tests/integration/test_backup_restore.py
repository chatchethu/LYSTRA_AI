import pytest
import sys
import os
import subprocess
import shutil
import glob

def run_bash_script(script_args):
    # On Windows, try to use bash if available (e.g. Git Bash, WSL). 
    # This allows testing the shell scripts locally.
    try:
        return subprocess.run(["bash"] + script_args, capture_output=True, text=True)
    except FileNotFoundError:
        # Fallback for some windows envs that map sh to bash
        return subprocess.run(["sh"] + script_args, capture_output=True, text=True)

@pytest.mark.skipif(sys.platform == 'win32', reason='Bash scripts not supported natively on Windows')
def test_db_backup_restore():
    print("=== Testing Database Backup & Restore ===")
    
    # Backup
    result = run_bash_script(["./scripts/backup_db.sh", "./backups/db"])
    assert result.returncode == 0, f"DB Backup failed:\nStdout: {result.stdout}\nStderr: {result.stderr}"
    
    # Find latest backup
    backups = glob.glob("./backups/db/db_backup_*.sql")
    assert len(backups) > 0, "No DB backup file found"
    latest_backup = max(backups, key=os.path.getctime)
    
    # Restore
    result = run_bash_script(["./scripts/restore_db.sh", latest_backup])
    assert result.returncode == 0, f"DB Restore failed:\nStdout: {result.stdout}\nStderr: {result.stderr}"
    
    print("DB Backup & Restore verified.")
    # cleanup
    os.remove(latest_backup)


@pytest.mark.skipif(sys.platform == 'win32', reason='Bash scripts not supported natively on Windows')
def test_files_backup_restore():
    print("=== Testing Files Backup & Restore ===")
    
    test_uploads = "./uploads_test_tmp"
    backup_dir = "./backups/files"
    
    # Setup dummy data
    os.makedirs(test_uploads, exist_ok=True)
    dummy_file = os.path.join(test_uploads, "dummy.txt")
    with open(dummy_file, "w") as f:
        f.write("test data")
        
    # Backup
    result = run_bash_script(["./scripts/backup_files.sh", test_uploads, backup_dir])
    assert result.returncode == 0, f"Files Backup failed:\nStdout: {result.stdout}\nStderr: {result.stderr}"
    
    # Find latest backup
    backups = glob.glob(f"{backup_dir}/files_backup_*.tar.gz")
    assert len(backups) > 0, "No files backup found"
    latest_backup = max(backups, key=os.path.getctime)
    
    # Wipe data
    shutil.rmtree(test_uploads)
    assert not os.path.exists(test_uploads)
    
    # Restore
    result = run_bash_script(["./scripts/restore_files.sh", latest_backup, test_uploads])
    assert result.returncode == 0, f"Files Restore failed:\nStdout: {result.stdout}\nStderr: {result.stderr}"
    
    # Verify data
    assert os.path.exists(dummy_file), "Restored dummy file not found"
    with open(dummy_file, "r") as f:
        assert f.read() == "test data", "Restored file content mismatch"
        
    print("Files Backup & Restore verified.")
    
    # Cleanup
    shutil.rmtree(test_uploads)
    os.remove(latest_backup)

if __name__ == "__main__":
    # Ensure backups directories exist
    os.makedirs("./backups/db", exist_ok=True)
    os.makedirs("./backups/files", exist_ok=True)
    
    try:
        test_db_backup_restore()
        test_files_backup_restore()
        print("=== All Backup & Restore tests passed ===")
    except Exception as e:
        print(f"Test failed: {e}")
        exit(1)
