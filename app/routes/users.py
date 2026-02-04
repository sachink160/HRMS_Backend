from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from typing import List, Optional
from app.database import get_db
from app.models import User, DocumentStatus, EmploymentHistory
from app.schema import (
    UserUpdate, UserResponse, FileUploadResponse,
    EmploymentHistoryResponse, EmployeeSummary
)
from app.auth import get_current_user, get_current_admin_user
from app.logger import log_info, log_error
from app.response import APIResponse
from app.storage import storage
import os

router = APIRouter(prefix="/users", tags=["users"])

def user_to_dict(user: User) -> dict:
    """Convert User model to dictionary for response."""
    # Get file URLs using storage service
    profile_image_url = storage.get_file_url(user.profile_image) if user.profile_image else None
    aadhaar_front_url = storage.get_file_url(user.aadhaar_front) if user.aadhaar_front else None
    aadhaar_back_url = storage.get_file_url(user.aadhaar_back) if user.aadhaar_back else None
    pan_image_url = storage.get_file_url(user.pan_image) if user.pan_image else None
    
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "phone": user.phone,
        "designation": user.designation,
        "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
        "is_active": user.is_active,
        "system_password": user.system_password,
        "profile_image": profile_image_url,
        "aadhaar_front": aadhaar_front_url,
        "aadhaar_back": aadhaar_back_url,
        "pan_image": pan_image_url,
        "profile_image_status": user.profile_image_status.value if user.profile_image_status else None,
        "aadhaar_front_status": user.aadhaar_front_status.value if user.aadhaar_front_status else None,
        "aadhaar_back_status": user.aadhaar_back_status.value if user.aadhaar_back_status else None,
        "pan_image_status": user.pan_image_status.value if user.pan_image_status else None,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        "department": user.department,
        "manager_id": user.manager_id,
        "joining_date": user.joining_date.isoformat() if user.joining_date else None,
    }

@router.get("/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile."""
    return APIResponse.success(
        data=user_to_dict(current_user),
        message="Profile retrieved successfully"
    )

@router.put("/profile")
async def update_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user's profile."""
    try:
        update_data = user_update.model_dump(exclude_unset=True)
        if not update_data:
            return APIResponse.success(
                data=user_to_dict(current_user),
                message="Profile retrieved successfully"
            )
        
        # Update user fields
        for field, value in update_data.items():
            setattr(current_user, field, value)
        
        await db.commit()
        await db.refresh(current_user)
        
        log_info(f"User profile updated: {current_user.email}")
        return APIResponse.success(
            data=user_to_dict(current_user),
            message="Profile updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Profile update error: {str(e)}")
        return APIResponse.internal_error(message="Profile update failed")

@router.get("/")
async def list_users(
    offset: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """List all users (admin only)."""
    try:
        from app.database import monitor_query
        
        async with monitor_query("list_users"):
            result = await db.execute(
                select(User)
                .offset(offset)
                .limit(limit)
                .order_by(User.created_at.desc())
            )
            users = result.scalars().all()
            users_data = [user_to_dict(user) for user in users]
            return APIResponse.success(
                data=users_data,
                message="Users retrieved successfully"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"List users error: {str(e)}")
        return APIResponse.internal_error(message="Failed to fetch users")

@router.get("/{user_id}")
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user by ID (admin only)."""
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            return APIResponse.not_found(message="User not found", resource="user")
        
        return APIResponse.success(
            data=user_to_dict(user),
            message="User retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Get user error: {str(e)}")
        return APIResponse.internal_error(message="Failed to fetch user")

@router.post("/upload-profile-image")
async def upload_profile_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload profile image."""
    try:
        # Delete old file if exists
        if current_user.profile_image:
            await storage.delete_file(current_user.profile_image)
        
        # Upload new file using storage service
        file_path = await storage.upload_file(file, current_user.id, "profile")
        
        # Read file size before updating
        file.seek(0)
        content = await file.read()
        file_size = len(content)
        
        # Update user record (profile photos are auto-approved)
        current_user.profile_image = file_path
        current_user.profile_image_status = DocumentStatus.APPROVED
        await db.commit()
        await db.refresh(current_user)
        
        log_info(f"Profile image uploaded for user: {current_user.email}")
        
        upload_data = {
            "filename": file.filename,
            "file_path": file_path,
            "file_url": storage.get_file_url(file_path),
            "file_size": file_size,
            "content_type": file.content_type or "application/octet-stream"
        }
        
        return APIResponse.success(
            data=upload_data,
            message="Profile image uploaded successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Profile image upload error: {str(e)}")
        return APIResponse.internal_error(message="Failed to upload profile image")

@router.post("/upload-aadhaar-front")
async def upload_aadhaar_front(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload Aadhaar front image."""
    try:
        # Delete old file if exists
        if current_user.aadhaar_front:
            await storage.delete_file(current_user.aadhaar_front)
        
        # Upload new file using storage service
        file_path = await storage.upload_file(file, current_user.id, "aadhaar_front")
        
        # Read file size before updating
        file.seek(0)
        content = await file.read()
        file_size = len(content)
        
        # Update user record
        current_user.aadhaar_front = file_path
        current_user.aadhaar_front_status = DocumentStatus.PENDING
        await db.commit()
        await db.refresh(current_user)
        
        log_info(f"Aadhaar front uploaded for user: {current_user.email}")
        
        upload_data = {
            "filename": file.filename,
            "file_path": file_path,
            "file_url": storage.get_file_url(file_path),
            "file_size": file_size,
            "content_type": file.content_type or "application/octet-stream"
        }
        
        return APIResponse.success(
            data=upload_data,
            message="Aadhaar front image uploaded successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Aadhaar front upload error: {str(e)}")
        return APIResponse.internal_error(message="Failed to upload Aadhaar front")

@router.post("/upload-aadhaar-back")
async def upload_aadhaar_back(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload Aadhaar back image."""
    try:
        # Delete old file if exists
        if current_user.aadhaar_back:
            await storage.delete_file(current_user.aadhaar_back)
        
        # Upload new file using storage service
        file_path = await storage.upload_file(file, current_user.id, "aadhaar_back")
        
        # Read file size before updating
        file.seek(0)
        content = await file.read()
        file_size = len(content)
        
        # Update user record
        current_user.aadhaar_back = file_path
        current_user.aadhaar_back_status = DocumentStatus.PENDING
        await db.commit()
        await db.refresh(current_user)
        
        log_info(f"Aadhaar back uploaded for user: {current_user.email}")
        
        upload_data = {
            "filename": file.filename,
            "file_path": file_path,
            "file_url": storage.get_file_url(file_path),
            "file_size": file_size,
            "content_type": file.content_type or "application/octet-stream"
        }
        
        return APIResponse.success(
            data=upload_data,
            message="Aadhaar back image uploaded successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Aadhaar back upload error: {str(e)}")
        return APIResponse.internal_error(message="Failed to upload Aadhaar back")

@router.post("/upload-pan")
async def upload_pan(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload PAN image."""
    try:
        # Delete old file if exists
        if current_user.pan_image:
            await storage.delete_file(current_user.pan_image)
        
        # Upload new file using storage service
        file_path = await storage.upload_file(file, current_user.id, "pan")
        
        # Read file size before updating
        file.seek(0)
        content = await file.read()
        file_size = len(content)
        
        # Update user record
        current_user.pan_image = file_path
        current_user.pan_image_status = DocumentStatus.PENDING
        await db.commit()
        await db.refresh(current_user)
        
        log_info(f"PAN uploaded for user: {current_user.email}")
        
        upload_data = {
            "filename": file.filename,
            "file_path": file_path,
            "file_url": storage.get_file_url(file_path),
            "file_size": file_size,
            "content_type": file.content_type or "application/octet-stream"
        }
        
        return APIResponse.success(
            data=upload_data,
            message="PAN image uploaded successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"PAN upload error: {str(e)}")
        return APIResponse.internal_error(message="Failed to upload PAN")

# Employee Management Endpoints for Users (now merged into User)
@router.get("/my-employee-details")
async def get_my_employee_details(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's employee details (read-only access)."""
    try:
        # Allow fetching self details even if account is inactive to keep dashboard/profile loads stable
        if not current_user.is_active:
            log_info(f"Inactive user {current_user.email} accessed their employee details (read-only)")

        log_info(f"User {current_user.email} (ID: {current_user.id}) accessing employee details (via merged User)")
        return APIResponse.success(
            data=user_to_dict(current_user),
            message="Employee details retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Get my employee details error: {str(e)}")
        return APIResponse.internal_error(message="Failed to fetch employee details")

@router.get("/my-employment-history")
async def get_my_employment_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's employment history (read-only access)."""
    try:
        # Allow read-only history for inactive users as well
        result = await db.execute(
            select(EmploymentHistory)
            .options(
                selectinload(EmploymentHistory.user),
                selectinload(EmploymentHistory.manager)
            )
            .where(EmploymentHistory.user_id == current_user.id)
            .order_by(EmploymentHistory.start_date.desc())
        )
        history = result.scalars().all()
        
        # Convert to dict
        history_data = [
            {
                "id": h.id,
                "user_id": h.user_id,
                "company_name": h.company_name,
                "position": h.position,
                "start_date": h.start_date.isoformat() if h.start_date else None,
                "end_date": h.end_date.isoformat() if h.end_date else None,
                "is_current": h.is_current,
                "manager_id": h.manager_id,
                "created_at": h.created_at.isoformat() if h.created_at else None,
            }
            for h in history
        ]
        
        # Log access for audit
        log_info(f"User {current_user.email} accessed their employment history")
        return APIResponse.success(
            data=history_data,
            message="Employment history retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Get my employment history error: {str(e)}")
        return APIResponse.internal_error(message="Failed to fetch employment history")

@router.get("/my-employee-summary")
async def get_my_employee_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's comprehensive employee summary (read-only access)."""
    try:
        # With merged model, details are on user
        employee_details = current_user

        # Get current position
        current_position_result = await db.execute(
            select(EmploymentHistory)
            .options(
                selectinload(EmploymentHistory.user),
                selectinload(EmploymentHistory.manager)
            )
            .where(
                and_(
                    EmploymentHistory.user_id == current_user.id,
                    EmploymentHistory.is_current == True
                )
            )
        )
        current_position = current_position_result.scalar_one_or_none()
        
        # Calculate work statistics (no tracking data available)
        total_work_days = 0
        total_hours = 0
        average_hours_per_day = 0
        
        # Log access for audit
        log_info(f"User {current_user.email} accessed their employee summary")
        
        summary_data = {
            "user": user_to_dict(current_user),
            "employee_details": user_to_dict(employee_details),
            "current_position": {
                "id": current_position.id,
                "company_name": current_position.company_name,
                "position": current_position.position,
                "start_date": current_position.start_date.isoformat() if current_position.start_date else None,
                "end_date": current_position.end_date.isoformat() if current_position.end_date else None,
                "is_current": current_position.is_current,
            } if current_position else None,
            "recent_tracking": [],
            "total_work_days": total_work_days,
            "average_hours_per_day": average_hours_per_day
        }
        
        return APIResponse.success(
            data=summary_data,
            message="Employee summary retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Get my employee summary error: {str(e)}")
        return APIResponse.internal_error(message="Failed to fetch employee summary")


@router.get("/my-department-colleagues")
async def get_my_department_colleagues(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get colleagues from the same department."""
    try:
        # Get current user's department
        # Department from merged User
        if not current_user.department:
            return APIResponse.success(
                data={"colleagues": [], "department": None},
                message="No department assigned"
            )
        
        # Get colleagues from same department
        colleagues_result = await db.execute(
            select(User)
            .where(
                and_(
                    User.department == current_user.department,
                    User.id != current_user.id,
                    User.is_active == True
                )
            )
        )
        colleagues = colleagues_result.scalars().all()
        
        colleagues_data = {
            "department": current_user.department,
            "colleagues": [
                {
                    "id": colleague.id,
                    "name": colleague.name,
                    "email": colleague.email,
                    "designation": colleague.designation,
                }
                for colleague in colleagues
            ]
        }
        
        return APIResponse.success(
            data=colleagues_data,
            message="Department colleagues retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Get department colleagues error: {str(e)}")
        return APIResponse.internal_error(message="Failed to fetch department colleagues")

@router.get("/my-manager")
async def get_my_manager(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's manager information."""
    try:
        # With merged model, manager_id is on User
        if not current_user.manager_id:
            return APIResponse.success(
                data={"manager": None},
                message="No manager assigned"
            )
        
        # Get manager details
        manager_result = await db.execute(
            select(User).where(User.id == current_user.manager_id)
        )
        manager = manager_result.scalar_one_or_none()
        
        if not manager:
            return APIResponse.success(
                data={"manager": None},
                message="Manager not found"
            )
        
        manager_data = {
            "manager": {
                "id": manager.id,
                "name": manager.name,
                "email": manager.email,
                "designation": manager.designation,
                "phone": manager.phone
            }
        }
        
        return APIResponse.success(
            data=manager_data,
            message="Manager information retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Get my manager error: {str(e)}")
        return APIResponse.internal_error(message="Failed to fetch manager information")
