"""
Password reset utility functions for secure token generation,
hashing, validation, and email sending.
"""
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models import PasswordResetToken, User
from app.logger import log_info, log_error


# Configuration
RESET_TOKEN_EXPIRY_MINUTES = 30
RESET_TOKEN_LENGTH = 32
MAX_RESET_REQUESTS_PER_HOUR = 3


def generate_reset_token() -> str:
    """
    Generate a cryptographically secure random token.
    
    Returns:
        str: 32-character random token
    """
    return secrets.token_urlsafe(RESET_TOKEN_LENGTH)


def hash_token(token: str) -> str:
    """
    Hash a token using SHA-256 for secure storage.
    
    Args:
        token: Plain text token
    
    Returns:
        str: Hexadecimal hash digest
    """
    return hashlib.sha256(token.encode()).hexdigest()


async def create_reset_token(db: AsyncSession, user_id: int) -> Optional[str]:
    """
    Create a new password reset token for a user.
    
    Args:
        db: Database session
        user_id: User ID to create token for
    
    Returns:
        str: Plain text token (only time it's available unhashed)
        None: If token creation failed
    """
    try:
        # Generate token
        token = generate_reset_token()
        token_hashed = hash_token(token)
        
        # Calculate expiry
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_EXPIRY_MINUTES)
        
        # Create database entry
        reset_token = PasswordResetToken(
            user_id=user_id,
            token_hash=token_hashed,
            expires_at=expires_at,
            is_used=False
        )
        
        db.add(reset_token)
        await db.commit()
        await db.refresh(reset_token)
        
        log_info(f"Password reset token created for user_id: {user_id}")
        return token
        
    except Exception as e:
        log_error(f"Failed to create reset token: {str(e)}")
        await db.rollback()
        return None


async def verify_reset_token(db: AsyncSession, token: str) -> Tuple[bool, Optional[User], str]:
    """
    Verify if a reset token is valid.
    
    Args:
        db: Database session
        token: Plain text token to verify
    
    Returns:
        Tuple of (is_valid, user_object, error_message)
    """
    try:
        token_hashed = hash_token(token)
        
        # Find token in database
        result = await db.execute(
            select(PasswordResetToken)
            .where(PasswordResetToken.token_hash == token_hashed)
        )
        reset_token = result.scalar_one_or_none()
        
        if not reset_token:
            return False, None, "Invalid or expired reset token"
        
        # Check if token is already used
        if reset_token.is_used:
            return False, None, "This reset link has already been used"
        
        # Check if token is expired
        if datetime.now(timezone.utc) > reset_token.expires_at:
            return False, None, "This reset link has expired"
        
        # Get user
        user_result = await db.execute(
            select(User).where(User.id == reset_token.user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            return False, None, "User not found"
        
        return True, user, ""
        
    except Exception as e:
        log_error(f"Error verifying reset token: {str(e)}")
        return False, None, "An error occurred while verifying the token"


async def mark_token_as_used(db: AsyncSession, token: str) -> bool:
    """
    Mark a reset token as used to prevent reuse.
    
    Args:
        db: Database session
        token: Plain text token to mark as used
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        token_hashed = hash_token(token)
        
        result = await db.execute(
            select(PasswordResetToken)
            .where(PasswordResetToken.token_hash == token_hashed)
        )
        reset_token = result.scalar_one_or_none()
        
        if reset_token:
            reset_token.is_used = True
            reset_token.used_at = datetime.now(timezone.utc)
            await db.commit()
            log_info(f"Reset token marked as used for user_id: {reset_token.user_id}")
            return True
        
        return False
        
    except Exception as e:
        log_error(f"Error marking token as used: {str(e)}")
        await db.rollback()
        return False


async def check_rate_limit(db: AsyncSession, user_id: int) -> bool:
    """
    Check if user has exceeded password reset request rate limit.
    
    Args:
        db: Database session
        user_id: User ID to check
    
    Returns:
        bool: True if within rate limit, False if exceeded
    """
    try:
        # Check requests in the last hour
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        
        result = await db.execute(
            select(PasswordResetToken)
            .where(
                and_(
                    PasswordResetToken.user_id == user_id,
                    PasswordResetToken.created_at >= one_hour_ago
                )
            )
        )
        tokens = result.scalars().all()
        
        if len(tokens) >= MAX_RESET_REQUESTS_PER_HOUR:
            log_info(f"Rate limit exceeded for user_id: {user_id}")
            return False
        
        return True
        
    except Exception as e:
        log_error(f"Error checking rate limit: {str(e)}")
        # On error, allow the request (fail open)
        return True


async def cleanup_expired_tokens(db: AsyncSession) -> int:
    """
    Clean up expired tokens from the database.
    This should be run periodically as a background task.
    
    Args:
        db: Database session
    
    Returns:
        int: Number of tokens deleted
    """
    try:
        # Delete tokens older than 24 hours
        twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)
        
        result = await db.execute(
            select(PasswordResetToken)
            .where(PasswordResetToken.created_at < twenty_four_hours_ago)
        )
        old_tokens = result.scalars().all()
        
        count = len(old_tokens)
        
        for token in old_tokens:
            await db.delete(token)
        
        await db.commit()
        
        if count > 0:
            log_info(f"Cleaned up {count} expired password reset tokens")
        
        return count
        
    except Exception as e:
        log_error(f"Error cleaning up expired tokens: {str(e)}")
        await db.rollback()
        return 0


def get_password_reset_email_html(user_name: str, reset_link: str) -> str:
    """
    Generate HTML content for password reset email.
    
    Args:
        user_name: Name of the user
        reset_link: Full URL to reset password page with token
    
    Returns:
        str: HTML email content
    """
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .container {{
            background-color: #f9fafb;
            border-radius: 8px;
            padding: 30px;
            border: 1px solid #e5e7eb;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .logo {{
            width: 60px;
            height: 60px;
            background-color: #2563eb;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 20px;
        }}
        h1 {{
            color: #1f2937;
            font-size: 24px;
            margin: 0;
        }}
        .content {{
            background-color: white;
            padding: 25px;
            border-radius: 6px;
            margin-bottom: 20px;
        }}
        .button {{
            display: inline-block;
            padding: 14px 28px;
            background-color: #2563eb;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
            margin: 20px 0;
        }}
        .button:hover {{
            background-color: #1d4ed8;
        }}
        .warning {{
            background-color: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 12px 16px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .footer {{
            text-align: center;
            color: #6b7280;
            font-size: 14px;
            margin-top: 20px;
        }}
        .link {{
            color: #2563eb;
            word-break: break-all;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">
                <svg width="30" height="30" viewBox="0 0 24 24" fill="white">
                    <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"></path>
                </svg>
            </div>
            <h1>Reset Your HRMS Password</h1>
        </div>
        
        <div class="content">
            <p>Hi <strong>{user_name}</strong>,</p>
            
            <p>We received a request to reset your password for your HRMS account. Click the button below to create a new password:</p>
            
            <div style="text-align: center;">
                <a href="{reset_link}" class="button">Reset Password</a>
            </div>
            
            <p>Or copy and paste this link into your browser:</p>
            <p class="link">{reset_link}</p>
            
            <div class="warning">
                <strong>⏱️ This link will expire in {RESET_TOKEN_EXPIRY_MINUTES} minutes</strong>
                <p style="margin: 5px 0 0 0; font-size: 14px;">For security reasons, you'll need to request a new link if it expires.</p>
            </div>
            
            <p><strong>Security reminder:</strong></p>
            <ul>
                <li>Never share this link with anyone</li>
                <li>Our team will never ask for your password</li>
                <li>If you didn't request this reset, please ignore this email</li>
            </ul>
        </div>
        
        <div class="footer">
            <p>This is an automated email from HRMS. Please do not reply to this email.</p>
            <p>&copy; 2026 HRMS. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""


def get_password_reset_confirmation_email_html(user_name: str) -> str:
    """
    Generate HTML content for password reset confirmation email.
    
    Args:
        user_name: Name of the user
    
    Returns:
        str: HTML email content
    """
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .container {{
            background-color: #f9fafb;
            border-radius: 8px;
            padding: 30px;
            border: 1px solid #e5e7eb;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .success-icon {{
            width: 60px;
            height: 60px;
            background-color: #10b981;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 20px;
        }}
        h1 {{
            color: #1f2937;
            font-size: 24px;
            margin: 0;
        }}
        .content {{
            background-color: white;
            padding: 25px;
            border-radius: 6px;
            margin-bottom: 20px;
        }}
        .alert {{
            background-color: #fef2f2;
            border-left: 4px solid #ef4444;
            padding: 12px 16px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .footer {{
            text-align: center;
            color: #6b7280;
            font-size: 14px;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="success-icon">
                <svg width="30" height="30" viewBox="0 0 24 24" fill="white" stroke="white" stroke-width="2">
                    <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
            </div>
            <h1>Password Successfully Reset</h1>
        </div>
        
        <div class="content">
            <p>Hi <strong>{user_name}</strong>,</p>
            
            <p>Your HRMS password has been successfully changed. You can now log in with your new password.</p>
            
            <div class="alert">
                <strong>⚠️ Didn't make this change?</strong>
                <p style="margin: 5px 0 0 0; font-size: 14px;">
                    If you didn't reset your password, please contact your administrator immediately and secure your account.
                </p>
            </div>
            
            <p><strong>Security tips:</strong></p>
            <ul>
                <li>Use a strong, unique password</li>
                <li>Don't share your password with anyone</li>
                <li>Change your password regularly</li>
                <li>Log out from shared devices</li>
            </ul>
        </div>
        
        <div class="footer">
            <p>This is an automated email from HRMS. Please do not reply to this email.</p>
            <p>&copy; 2026 HRMS. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
