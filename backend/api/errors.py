from fastapi import HTTPException
from backend.schemas.errors import ErrorCode

class APIException(HTTPException):
    def __init__(self, code: ErrorCode, message: str, status_code: int = 400, details: dict = None):
        super().__init__(status_code=status_code, detail={"code": code.value, "message": message, "details": details or {}})


class RateLimitError(HTTPException):
    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(status_code=429, detail=detail)


class LystraError(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
