from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from backend.schemas.user import UserCreate, UserUpdate, UserResponse, Token, TokenRefresh
from backend.crud import user
from backend.auth.dependencies import get_db_session, get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

from backend.auth.service import AuthService

auth_service = AuthService()

@router.post("/register", response_model=Token)
async def register(
    user_in: UserCreate,
    response: Response,
    db: AsyncSession = Depends(get_db_session)
):
    existing_user = await user.get_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    existing_username = await user.get_by_username(db, username=user_in.username)
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")
        
    new_user = await user.create_with_password(db, obj_in=user_in)
    
    access_token = auth_service.create_access_token(new_user.id, new_user.email)
    refresh_token = auth_service.create_refresh_token(new_user.id)
    
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite='lax', max_age=604800)
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=False, samesite='lax', max_age=2592000)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": str(new_user.id),
            "email": new_user.email,
            "username": new_user.username
        }
    }

from fastapi.security import OAuth2PasswordRequestForm

@router.post("/login", response_model=Token)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db_session)
):
    auth_user = await user.authenticate(db, email=form_data.username, password=form_data.password)
    if not auth_user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    access_token = auth_service.create_access_token(auth_user.id, auth_user.email)
    refresh_token = auth_service.create_refresh_token(auth_user.id)
    
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite='lax', max_age=604800)
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=False, samesite='lax', max_age=2592000)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": str(auth_user.id),
            "email": auth_user.email,
            "username": auth_user.username
        }
    }

@router.post("/refresh", response_model=UserResponse)
async def refresh_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db_session)
):
    try:
        refresh_token = request.cookies.get("refresh_token")
        if not refresh_token:
            raise HTTPException(status_code=401, detail="No refresh token cookie found")
            
        new_access, new_refresh = await auth_service.refresh_tokens(refresh_token, db)
        
        response.set_cookie(key="access_token", value=f"Bearer {new_access}", httponly=True, secure=False, samesite='lax', max_age=604800)
        response.set_cookie(key="refresh_token", value=new_refresh, httponly=True, secure=False, samesite='lax', max_age=2592000)
        
        payload = auth_service.decode_token(new_access)
        from uuid import UUID as _UUID
        from backend.crud import user as crud_user
        db_user = await crud_user.get(db, id=_UUID(payload["sub"]))
        return db_user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@router.post("/logout")
async def logout(request: Request, response: Response):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        try:
            await auth_service.revoke_refresh_token(refresh_token)
        except Exception:
            pass
            
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"msg": "Successfully logged out"}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return current_user

@router.patch("/me", response_model=UserResponse)
async def update_me(
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserResponse = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return await user.update(db, db_obj=current_user, obj_in=user_update)
