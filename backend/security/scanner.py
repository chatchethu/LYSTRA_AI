import re

class SecretScanner:
    """
    CQ-33, CQ-37: Secret Protection and Response Sanitization.
    Scans for and redacts API keys, JWTs, Passwords, DB URLs.
    """
    
    PATTERNS = {
        "JWT": re.compile(r"ey[a-zA-Z0-9_-]{10,}\.ey[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}"),
        # Basic OpenAI Key
        "OPENAI_KEY": re.compile(r"sk-[a-zA-Z0-9]{32,}"),
        # Basic DB URL with credentials
        "DB_URL": re.compile(r"(postgres|postgresql|mysql|redis)://[a-zA-Z0-9_-]+:[^@\s]+@[a-zA-Z0-9.-]+(:\d+)?")
    }

    @classmethod
    def sanitize(cls, text: str) -> str:
        if not text:
            return text
            
        sanitized = text
        for name, pattern in cls.PATTERNS.items():
            sanitized = pattern.sub("[REDACTED]", sanitized)
            
        return sanitized

    @classmethod
    def contains_secrets(cls, text: str) -> bool:
        if not text:
            return False
            
        for pattern in cls.PATTERNS.values():
            if pattern.search(text):
                return True
        return False
