from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta
from app.database import get_db
from app.models import User
from app.schema import UserCreate, UserResponse, UserLogin, UserUpdate, AdminCreateWithSecret, PasswordChange, ForgotPasswordRequest, ResetPasswordRequest
from app.models import UserRole
from app.auth import (
    get_password_hash, 
    verify_password,
    authenticate_user, 
    create_access_token, 
    get_current_user,
    get_current_admin_user,
    get_user_by_email,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.logger import log_info, log_error
from app.response import APIResponse
import os

router = APIRouter(prefix="/auth", tags=["authentication"])

# Secret codes from environment variables
ADMIN_SECRET_CODE = os.getenv("ADMIN_SECRET_CODE")

@router.post("/register")
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    try:
        # Check if user already exists
        existing_user = await db.execute(select(User).where(User.email == user.email))
        if existing_user.scalar_one_or_none():
            return APIResponse.bad_request(message="Email already registered")
        
        # Create new user with default USER role
        hashed_password = get_password_hash(user.password)
        db_user = User(
            email=user.email,
            hashed_password=hashed_password,
            name=user.name,
            phone=user.phone,
            designation=user.designation,
            joining_date=user.joining_date,
            role=UserRole.USER  # Default role is USER
        )
        
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        
        log_info(f"New user registered: {user.email} with role: {db_user.role}")
        
        # Convert user to dict for response
        user_data = {
            "id": db_user.id,
            "email": db_user.email,
            "name": db_user.name,
            "phone": db_user.phone,
            "designation": db_user.designation,
            "role": db_user.role.value,
            "is_active": db_user.is_active,
            "created_at": db_user.created_at.isoformat() if db_user.created_at else None,
            "updated_at": db_user.updated_at.isoformat() if db_user.updated_at else None
        }
        
        return APIResponse.created(
            data=user_data,
            message="User registered successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Registration error: {str(e)}")
        return APIResponse.internal_error(message="Registration failed")

@router.post("/login")
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login user and return access token with user data."""
    try:
        # First check if user exists and is active
        user = await get_user_by_email(db, login_data.email)
        if not user:
            return APIResponse.unauthorized(message="Incorrect email or password")
        
        if not user.is_active:
            return APIResponse.unauthorized(message="Account is deactivated. Please contact administrator.")
        
        # Now authenticate with password
        user = await authenticate_user(db, login_data.email, login_data.password)
        if not user:
            return APIResponse.unauthorized(message="Incorrect email or password")
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        log_info(f"User logged in: {user.email}")
        
        login_data = {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "phone": user.phone,
                "role": user.role.value,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None
            }
        }
        
        return APIResponse.success(
            data=login_data,
            message="Login successful"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Login error: {str(e)}")
        return APIResponse.internal_error(message="Login failed")

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout current user."""
    try:
        log_info(f"User logged out: {current_user.email}")
        
        return APIResponse.success(
            data={"message": "Logged out successfully"},
            message="Logged out successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Logout error: {str(e)}")
        return APIResponse.internal_error(message="Logout failed")

@router.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    user_data = {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "phone": current_user.phone,
        "designation": current_user.designation,
        "role": current_user.role.value,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        "updated_at": current_user.updated_at.isoformat() if current_user.updated_at else None
    }
    return APIResponse.success(
        data=user_data,
        message="User information retrieved successfully"
    )

@router.get("/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile."""
    user_data = {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "phone": current_user.phone,
        "designation": current_user.designation,
        "role": current_user.role.value,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        "updated_at": current_user.updated_at.isoformat() if current_user.updated_at else None
    }
    return APIResponse.success(
        data=user_data,
        message="Profile retrieved successfully"
    )

@router.put("/profile")
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
        if user_update.designation is not None:
            current_user.designation = user_update.designation
        if user_update.joining_date is not None:
            current_user.joining_date = user_update.joining_date
        if user_update.system_password is not None:
            current_user.system_password = user_update.system_password
        
        await db.commit()
        await db.refresh(current_user)
        
        log_info(f"User profile updated: {current_user.email}")
        
        user_data = {
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.name,
            "phone": current_user.phone,
            "designation": current_user.designation,
            "role": current_user.role.value,
            "is_active": current_user.is_active,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
            "updated_at": current_user.updated_at.isoformat() if current_user.updated_at else None
        }
        
        return APIResponse.success(
            data=user_data,
            message="Profile updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Profile update error: {str(e)}")
        return APIResponse.internal_error(message="Profile update failed")

@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change password for current user (works for both employees and admins)."""
    try:
        # Verify current password
        if not verify_password(password_data.current_password, current_user.hashed_password):
            return APIResponse.bad_request(message="Current password is incorrect")
        
        # Check if new password is different from current password
        if verify_password(password_data.new_password, current_user.hashed_password):
            return APIResponse.bad_request(message="New password must be different from current password")
        
        # Update password
        current_user.hashed_password = get_password_hash(password_data.new_password)
        await db.commit()
        await db.refresh(current_user)
        
        log_info(f"Password changed for user: {current_user.email}")
        
        return APIResponse.success(
            data={"message": "Password changed successfully"},
            message="Password changed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Password change error: {str(e)}")
        return APIResponse.internal_error(message="Password change failed")

@router.post("/register-admin")
async def register_admin(
    user: UserCreate, 
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Register a new admin user (admin only)."""
    try:
        # Check if user already exists
        existing_user = await db.execute(select(User).where(User.email == user.email))
        if existing_user.scalar_one_or_none():
            return APIResponse.bad_request(message="Email already registered")
        
        # Create new admin user
        hashed_password = get_password_hash(user.password)
        db_user = User(
            email=user.email,
            hashed_password=hashed_password,
            name=user.name,
            phone=user.phone,
            designation=user.designation,
            joining_date=user.joining_date,
            role=UserRole.ADMIN  # Admin role
        )
        
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        
        log_info(f"New admin user registered: {user.email} by admin: {current_user.email}")
        
        user_data = {
            "id": db_user.id,
            "email": db_user.email,
            "name": db_user.name,
            "phone": db_user.phone,
            "designation": db_user.designation,
            "role": db_user.role.value,
            "is_active": db_user.is_active,
            "created_at": db_user.created_at.isoformat() if db_user.created_at else None,
            "updated_at": db_user.updated_at.isoformat() if db_user.updated_at else None
        }
        
        return APIResponse.created(
            data=user_data,
            message="Admin user registered successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Admin registration error: {str(e)}")
        return APIResponse.internal_error(message="Admin registration failed")

@router.post("/create-admin")
async def create_admin_with_secret(
    admin_data: AdminCreateWithSecret,
    db: AsyncSession = Depends(get_db)
):
    """
    Create admin user with secret code validation.
    No authentication required, but secret code must match backend configuration.
    """
    try:
        # Validate role - only admin is allowed
        if admin_data.role != UserRole.ADMIN:
            return APIResponse.bad_request(message="Role must be 'admin'")
        
        # Validate secret code
        if admin_data.secret_code != ADMIN_SECRET_CODE:
            log_error(f"Invalid admin secret code attempt for email: {admin_data.email}")
            return APIResponse.forbidden(message="Invalid secret code for admin creation")
        
        # Check if user already exists
        existing_user = await db.execute(select(User).where(User.email == admin_data.email))
        if existing_user.scalar_one_or_none():
            return APIResponse.bad_request(message="Email already registered")
        
        # Validate password strength
        if len(admin_data.password) < 8:
            return APIResponse.bad_request(message="Password must be at least 8 characters long")
        
        # Create new admin user
        hashed_password = get_password_hash(admin_data.password)
        db_user = User(
            email=admin_data.email,
            hashed_password=hashed_password,
            name=admin_data.name,
            phone=admin_data.phone,
            designation=admin_data.designation,
            joining_date=admin_data.joining_date,
            role=UserRole.ADMIN,
            is_active=True
        )
        
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        
        log_info(f"New admin user created: {admin_data.email} via secret code")
        
        user_data = {
            "id": db_user.id,
            "email": db_user.email,
            "name": db_user.name,
            "phone": db_user.phone,
            "designation": db_user.designation,
            "role": db_user.role.value,
            "is_active": db_user.is_active,
            "created_at": db_user.created_at.isoformat() if db_user.created_at else None,
            "updated_at": db_user.updated_at.isoformat() if db_user.updated_at else None
        }
        
        return APIResponse.created(
            data=user_data,
            message="Admin user created successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Create admin with secret code error: {str(e)}")
        return APIResponse.internal_error(message="Failed to create admin user")

# Password Reset Endpoints
@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Request a password reset email.
    Always returns success message for security (doesn't reveal if email exists).
    """
    try:
        from app.password_reset_utils import create_reset_token, check_rate_limit, get_password_reset_email_html
        from app.email_service import email_service
        
        # Try to find user by email
        user_result = await db.execute(select(User).where(User.email == request.email))
        user = user_result.scalar_one_or_none()
        
        # Always return success message (security: don't reveal if email exists)
        success_message = "If an account with that email exists, we've sent a password reset link."
        
        if not user:
            # Email doesn't exist, but return success message anyway
            log_info(f"Password reset requested for non-existent email: {request.email}")
            return APIResponse.success(
                data={"message": success_message},
                message=success_message
            )
        
        # Check rate limiting
        if not await check_rate_limit(db, user.id):
            return APIResponse.bad_request(
                message="Too many password reset requests. Please try again later."
            )
        
        # Generate reset token
        token = await create_reset_token(db, user.id)
        
        if not token:
            log_error(f"Failed to generate reset token for user: {request.email}")
            return APIResponse.internal_error(message="Failed to process password reset request")
        
        # Load email settings
        await email_service.load_settings(db)
        
        # Create reset link (adjust URL based on your frontend deployment)
        # TODO: Update this URL to match your production frontend URL
        frontend_url = "http://localhost:5173"  # Development URL
        reset_link = f"{frontend_url}/reset-password?token={token}"
        
        # Generate email HTML
        email_html = get_password_reset_email_html(user.name, reset_link)
        
        # Send email
        email_sent = await email_service.send_email(
            db=db,
            recipient_email=user.email,
            subject="Reset Your HRMS Password",
            body=email_html,
            recipient_name=user.name,
            template_type="password_reset"
        )
        
        if not email_sent:
            log_error(f"Failed to send password reset email to: {request.email}")
            # Still return success to user (don't reveal failure)
        else:
            log_info(f"Password reset email sent to: {request.email}")
        
        return APIResponse.success(
            data={"message": success_message},
            message=success_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Forgot password error: {str(e)}")
        return APIResponse.internal_error(message="Failed to process password reset request")

@router.get("/verify-reset-token/{token}")
async def verify_reset_token_endpoint(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify if a password reset token is valid.
    Used by frontend before showing the reset password form.
    """
    try:
        from app.password_reset_utils import verify_reset_token
        from app.schema import VerifyResetTokenResponse
        
        is_valid, user, error_message = await verify_reset_token(db, token)
        
        if is_valid:
            return APIResponse.success(
                data=VerifyResetTokenResponse(valid=True, message="Token is valid").dict(),
                message="Token is valid"
            )
        else:
            return APIResponse.bad_request(
                message=error_message,
                data=VerifyResetTokenResponse(valid=False, message=error_message).dict()
            )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Verify reset token error: {str(e)}")
        return APIResponse.internal_error(message="Failed to verify token")

@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Reset password using a valid reset token.
    """
    try:
        from app.password_reset_utils import verify_reset_token, mark_token_as_used, get_password_reset_confirmation_email_html
        from app.email_service import email_service
        
        # Verify token
        is_valid, user, error_message = await verify_reset_token(db, request.token)
        
        if not is_valid:
            return APIResponse.bad_request(message=error_message)
        
        # Update password
        user.hashed_password = get_password_hash(request.new_password)
        await db.commit()
        await db.refresh(user)
        
        # Mark token as used
        await mark_token_as_used(db, request.token)
        
        log_info(f"Password reset successful for user: {user.email}")
        
        # Send confirmation email
        try:
            await email_service.load_settings(db)
            email_html = get_password_reset_confirmation_email_html(user.name)
            
            await email_service.send_email(
                db=db,
                recipient_email=user.email,
                subject="Your HRMS Password Has Been Reset",
                body=email_html,
                recipient_name=user.name,
                template_type="password_reset_confirmation"
            )
        except Exception as email_error:
            log_error(f"Failed to send password reset confirmation email: {str(email_error)}")
            # Continue even if confirmation email fails
        
        return APIResponse.success(
            data={"message": "Password has been reset successfully"},
            message="Password has been reset successfully. You can now log in with your new password."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Reset password error: {str(e)}")
        return APIResponse.internal_error(message="Failed to reset password")

