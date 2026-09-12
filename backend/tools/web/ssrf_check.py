import ipaddress
import socket
import asyncio
from urllib.parse import urlparse

class SSRFBlockedError(ValueError): pass
class InvalidURLError(ValueError): pass

def is_internal_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
        # Fix #6: Block unspecified (0.0.0.0) alongside private, loopback, link-local, multicast, reserved
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified:
            return True
        # Explicitly block AWS metadata endpoint
        if str(ip) == "169.254.169.254":
            return True
        return False
    except ValueError:
        return False

async def validate_url(url: str) -> str:
    """
    Validates a URL against SSRF attacks.
    Returns the resolved, safe IP address to be used for the actual connection 
    to prevent DNS rebinding attacks.
    """
    parsed = urlparse(url)
    
    # Fix #5: Distinct exception types for monitoring
    if parsed.scheme not in ('http', 'https'):
        raise InvalidURLError(f"Invalid scheme: {parsed.scheme}")
        
    hostname = parsed.hostname
    if not hostname:
        raise InvalidURLError("No hostname in URL")
        
    # Fix #3: Async DNS resolution
    loop = asyncio.get_running_loop()
    try:
        addr_info = await loop.getaddrinfo(hostname, None)
    except socket.gaierror:
        raise InvalidURLError(f"DNS resolution failed for {hostname}")
        
    safe_ip = None
    for res in addr_info:
        ip = res[4][0]
        if is_internal_ip(ip):
            raise SSRFBlockedError(f"URL resolves to internal/blocked IP: {ip}")
        if not safe_ip:
            safe_ip = ip
            
    # Fix #2: Return the validated IP so the caller can pin the connection
    return safe_ip
