
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token
from app.core.dependencies import get_current_active_user, get_token_from_header
from app.core.rate_limit import limiter, AUTH_RATE_LIMIT
from app.core.token_blacklist import TokenBlacklist
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.services.user_service import UserService, get_user_service
from app.config import settings

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(AUTH_RATE_LIMIT)
async def register(
    request: Request,
    user: UserCreate, 
    db: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(get_user_service)
):
    db_user = await user_service.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    if user.email:
        db_user = await user_service.get_user_by_email(db, email=user.email)
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    return await user_service.create_user(db=db, user=user)


@router.post("/login", response_model=Token)
@limiter.limit(AUTH_RATE_LIMIT)
async def login(
    request: Request,
    user_login: UserLogin, 
    db: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(get_user_service)
):
    user = await user_service.authenticate_user(db, username=user_login.username, password=user_login.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: UserResponse = Depends(get_current_active_user)):
    return current_user


@router.post("/logout")
async def logout(
    token: str = Depends(get_token_from_header),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """用户登出
    
    将当前 Token 加入黑名单，使其立即失效。
    """
    await TokenBlacklist.add(token)
    return {"message": "Successfully logged out"}
