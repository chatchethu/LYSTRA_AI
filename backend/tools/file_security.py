import os
from pathlib import Path
from typing import Optional
from uuid import UUID

class FileSecurityViolation(Exception):
    pass

class FileStorageManager:
    """
    Phase 30: Strict File Storage isolation.
    """
    def __init__(self, base_storage_dir: str = "storage"):
        self.base_dir = Path(base_storage_dir).resolve()
        
    def resolve_safe_path(self, user_id: UUID, requested_path: str) -> Path:
        """
        Validates and isolates a path to storage/{user_id}/{filename}
        Prevents ../, absolute paths, and symlink traversal.
        """
        # Strip all absolute anchors and directory traversal attempts
        requested_path = requested_path.replace("\\", "/")
        
        if "../" in requested_path or ".." in requested_path.split("/"):
            raise FileSecurityViolation("Path traversal attack detected.")
            
        filename = requested_path.split("/")[-1]
        
        if not filename or filename in [".", ".."]:
            raise FileSecurityViolation("Invalid filename requested.")
            
        # The true isolated directory
        user_storage = (self.base_dir / str(user_id)).resolve()
        
        # Ensure user directory exists
        user_storage.mkdir(parents=True, exist_ok=True)
        
        # Target path
        safe_path = (user_storage / filename).resolve()
        
        # Strict prefix check to prevent any escape
        if not str(safe_path).startswith(str(user_storage)):
            raise FileSecurityViolation("Path traversal attack detected.")
            
        return safe_path

    def write_file(self, user_id: UUID, filename: str, content: str) -> str:
        safe_path = self.resolve_safe_path(user_id, filename)
        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(content)
        return str(safe_path)

    def read_file(self, user_id: UUID, filename: str) -> str:
        safe_path = self.resolve_safe_path(user_id, filename)
        if not safe_path.exists():
            raise FileSecurityViolation("File does not exist.")
        if safe_path.is_symlink():
            raise FileSecurityViolation("Symlinks are explicitly forbidden.")
            
        with open(safe_path, "r", encoding="utf-8") as f:
            return f.read()
