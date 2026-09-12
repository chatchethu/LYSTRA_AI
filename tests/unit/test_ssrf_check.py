import pytest
from backend.tools.web.ssrf_check import validate_url, is_internal_ip

def test_is_internal_ip():
    assert is_internal_ip("127.0.0.1") is True
    assert is_internal_ip("192.168.1.1") is True
    assert is_internal_ip("10.0.0.1") is True
    assert is_internal_ip("169.254.169.254") is True
    assert is_internal_ip("8.8.8.8") is False
    assert is_internal_ip("1.1.1.1") is False

def test_validate_url_valid():
    # Should not raise exception
    validate_url("https://example.com")
    validate_url("http://google.com")

def test_validate_url_invalid_scheme():
    with pytest.raises(ValueError, match="Invalid scheme"):
        validate_url("file:///etc/passwd")
    
    with pytest.raises(ValueError, match="Invalid scheme"):
        validate_url("ftp://example.com")

def test_validate_url_internal():
    with pytest.raises(ValueError, match="internal/blocked IP"):
        validate_url("http://localhost")
        
    with pytest.raises(ValueError, match="internal/blocked IP"):
        validate_url("http://127.0.0.1")
        
    with pytest.raises(ValueError, match="internal/blocked IP"):
        validate_url("http://169.254.169.254/latest/meta-data/")
