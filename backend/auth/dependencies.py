from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.config import get_settings
from backend.db.session import get_db
from backend.llm.gateway import LLMGateway

settings = get_settings()

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db():
        yield session

def get_llm_gateway() -> LLMGateway:
    from backend.main import llm_gateway
    if not llm_gateway:
        raise HTTPException(status_code=500, detail="LLM Gateway not initialized")
    return llm_gateway

from uuid import UUID
from backend.crud.user import user as crud_user
from backend.db.models.user import User
from backend.schemas.user import UserCreate

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db_session)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Try cookie first, fallback to header (for API clients, scripts)
    token_str = request.cookies.get("access_token")
    if not token_str:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token_str = auth_header[7:]
    
    print(
        f"get_current_user DEBUG: path={request.url.path}, "
        f"token_present={bool(token_str)}"
    )
            
    if not token_str:
        raise credentials_exception
        
    token = token_str
        
    from backend.auth.token_blocklist import is_jti_blocked
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        
        # Must be an access token, not a refresh token
        if payload.get("type") != "access":
            raise credentials_exception
            
        # Check blocklist
        jti = payload.get("jti")
        if await is_jti_blocked(jti):
            raise credentials_exception
            
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = UUID(user_id_str)
    except (jwt.PyJWTError, ValueError):
        raise credentials_exception
        
    db_user = await crud_user.get(db, id=user_id)
    if db_user is None or not db_user.is_active:
        raise credentials_exception
    return db_user

async def get_optional_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db_session)
) -> User:
    try:
        return await get_current_user(request=request, db=db)
    except HTTPException:
        pass
            
    # Fallback to Guest User
    guest_email = "guest@lystra.ai"
    result = await db.execute(select(User).filter(User.email == guest_email))
    guest_user = result.scalars().first()
    
    if not guest_user:
        guest_in = UserCreate(email=guest_email, username="guest", password="guestpassword123")
        guest_user = await crud_user.create_with_password(db, obj_in=guest_in)
        
    return guest_user

def require_permission(permission: str):
    async def permission_checker(current_user: User = Depends(get_current_user)):
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Requires {permission}"
            )
        return current_user
    return permission_checker
