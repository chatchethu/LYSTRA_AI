import pytest
import uuid
from backend.tools.file_security import FileStorageManager, FileSecurityViolation

def test_file_security_path_traversal():
    manager = FileStorageManager()
    user_id = uuid.uuid4()
    
    with pytest.raises(FileSecurityViolation):
        manager.resolve_safe_path(user_id, "../../../etc/passwd")
        
def test_file_security_absolute_path():
    manager = FileStorageManager()
    user_id = uuid.uuid4()
    
    # Should strip the absolute path and just use the filename
    safe_path = manager.resolve_safe_path(user_id, "/etc/passwd")
    assert safe_path.name == "passwd"
    assert "etc" not in safe_path.parts
    assert str(user_id) in str(safe_path)

def test_file_security_valid_path():
    manager = FileStorageManager()
    user_id = uuid.uuid4()
    
    safe_path = manager.resolve_safe_path(user_id, "my_script.py")
    assert safe_path.name == "my_script.py"
    assert str(user_id) in str(safe_path)
