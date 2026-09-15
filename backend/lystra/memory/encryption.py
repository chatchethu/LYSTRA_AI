import base64
import os
import structlog
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from backend.config import get_settings

logger = structlog.get_logger(__name__)

class MemoryEncryption:
    def __init__(self):
        settings = get_settings()
        try:
            salt = b'lystra_memory_salt'
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(settings.SECRET_KEY.encode()))
            self.fernet = Fernet(key)
            self.enabled = True
        except Exception as e:
            logger.error('memory_encryption_init_failed', error=str(e))
            self.enabled = False

    def encrypt(self, text: str) -> str:
        if not self.enabled or not text:
            return text
        try:
            return self.fernet.encrypt(text.encode()).decode()
        except Exception as e:
            logger.error('memory_encryption_failed', error=str(e))
            return text

    def decrypt(self, encrypted_text: str) -> str:
        if not self.enabled or not encrypted_text:
            return encrypted_text
        
        if not encrypted_text.startswith('gAAAAAB'):
            return encrypted_text
            
        try:
            return self.fernet.decrypt(encrypted_text.encode()).decode()
        except Exception as e:
            logger.error('memory_decryption_failed', error=str(e))
            return encrypted_text
