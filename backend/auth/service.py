from datetime import datetime, timedelta, timezone
from typing import Tuple
from uuid import UUID
import bcrypt
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt

from backend.config import get_settings

settings = get_settings()

SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
# Access token: 7 days so users stay logged in comfortably
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7   # 7 days
# Refresh token: 30 days
REFRESH_TOKEN_EXPIRE_DAYS = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

class AuthService:
    """
    JWT-based authentication with refresh token rotation.
    Passwords hashed with bcrypt.
    """
    
    def hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        
    def verify_password(self, plain: str, hashed: str) -> bool:
        return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
        
    def create_access_token(self, user_id: UUID, email: str, scopes: list[str] = None) -> str:
        import uuid
        to_encode = {"sub": str(user_id), "email": email, "scopes": scopes or [], "type": "access", "jti": str(uuid.uuid4())}
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
    def create_refresh_token(self, user_id: UUID) -> str:
        import uuid
        to_encode = {"sub": str(user_id), "type": "refresh", "jti": str(uuid.uuid4())}
        expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
    def decode_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
            )
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
            
    async def refresh_tokens(self, refresh_token: str, db) -> Tuple[str, str]:
        """
        Validate refresh token, look up the real user, and return a fresh token pair.
        """
        from backend.auth.token_blocklist import is_jti_blocked, block_token_jti
        payload = self.decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=400, detail="Invalid token type")
            
        jti = payload.get("jti")
        if await is_jti_blocked(jti):
             raise HTTPException(status_code=401, detail="Token revoked")
        
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(status_code=401, detail="Invalid refresh token: missing subject")
        
        try:
            user_id = UUID(user_id_str)
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid refresh token: bad user ID")
        
        # Load the real user from DB
        from sqlalchemy import select
        from backend.db.models.user import User
        result = await db.execute(select(User).where(User.id == user_id))
        db_user = result.scalar_one_or_none()
        
        if not db_user or not db_user.is_active:
            raise HTTPException(status_code=401, detail="User not found or inactive")
            
        # Revoke the old refresh token
        exp = payload.get("exp")
        if exp:
            expires_in = int(exp - datetime.now(timezone.utc).timestamp())
            if expires_in > 0:
                await block_token_jti(jti, expires_in)
        
        # Issue fresh token pair
        new_access = self.create_access_token(db_user.id, db_user.email)
        new_refresh = self.create_refresh_token(db_user.id)
        return new_access, new_refresh
        
    async def revoke_refresh_token(self, token: str):
        from backend.auth.token_blocklist import block_token_jti
        payload = self.decode_token(token)
        jti = payload.get("jti")
        exp = payload.get("exp")
        if jti and exp:
            expires_in = int(exp - datetime.now(timezone.utc).timestamp())
            if expires_in > 0:
                await block_token_jti(jti, expires_in)
        
    async def is_token_revoked(self, token: str) -> bool:
        from backend.auth.token_blocklist import is_jti_blocked
        payload = self.decode_token(token)
        return await is_jti_blocked(payload.get("jti"))

