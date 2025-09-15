from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta
from app.database import get_db
from app.models import User
from app.schema import UserCreate, UserResponse, UserLogin, UserUpdate
from app.models import UserRole
from app.auth import (
    get_password_hash, 
    authenticate_user, 
    create_access_token, 
    get_current_user,
    get_current_super_admin_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.logger import log_info, log_error

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    try:
        # Check if user already exists
        existing_user = await db.execute(select(User).where(User.email == user.email))
        if existing_user.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user with default USER role
        hashed_password = get_password_hash(user.password)
        db_user = User(
            email=user.email,
            hashed_password=hashed_password,
            name=user.name,
            phone=user.phone,
            role=UserRole.USER  # Default role is USER
        )
        
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        
        log_info(f"New user registered: {user.email} with role: {db_user.role}")
        return db_user
        
    except Exception as e:
        log_error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/login", response_model=dict)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login user and return access token with user data."""
    try:
        user = await authenticate_user(db, login_data.email, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        log_info(f"User logged in: {user.email}")
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "phone": user.phone,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at,
                "updated_at": user.updated_at
            }
        }
        
    except Exception as e:
        log_error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user

@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile."""
    return current_user

@router.put("/profile", response_model=UserResponse)
async def update_profile(
    user_update: UserUpdate, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user profile."""
    try:
        if user_update.name is not None:
            current_user.name = user_update.name
        if user_update.phone is not None:
            current_user.phone = user_update.phone
        
        await db.commit()
        await db.refresh(current_user)
        
        log_info(f"User profile updated: {current_user.email}")
        return current_user
        
    except Exception as e:
        log_error(f"Profile update error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )

@router.post("/register-admin", response_model=UserResponse)
async def register_admin(
    user: UserCreate, 
    current_user: User = Depends(get_current_super_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Register a new admin user (super admin only)."""
    try:
        # Check if user already exists
        existing_user = await db.execute(select(User).where(User.email == user.email))
        if existing_user.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new admin user
        hashed_password = get_password_hash(user.password)
        db_user = User(
            email=user.email,
            hashed_password=hashed_password,
            name=user.name,
            phone=user.phone,
            role=UserRole.ADMIN  # Admin role
        )
        
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        
        log_info(f"New admin user registered: {user.email} by super admin: {current_user.email}")
        return db_user
        
    except Exception as e:
        log_error(f"Admin registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin registration failed"
        )
