from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from typing import List, Optional
from app.database import get_db
from app.models import User, DocumentStatus, EmployeeDetails, EmploymentHistory
from app.schema import (
    UserUpdate, UserResponse, FileUploadResponse,
    EmployeeDetailsResponse, EmploymentHistoryResponse, EmployeeSummary
)
from app.auth import get_current_user, get_current_admin_user
from app.logger import log_info, log_error
import os
import uuid
from pathlib import Path
from typing import Optional

router = APIRouter(prefix="/users", tags=["users"])

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Allowed file types for identity documents
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def validate_file(file: UploadFile) -> bool:
    """Validate uploaded file type and size."""
    if not file.filename:
        return False
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return False
    
    return True

async def save_uploaded_file(file: UploadFile, user_id: int, document_type: str) -> str:
    """Save uploaded file and return the file path."""
    if not validate_file(file):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only JPG, PNG, and PDF files are allowed."
        )
    
    # Generate unique filename
    file_ext = Path(file.filename).suffix.lower()
    unique_filename = f"{user_id}_{document_type}_{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Read file content
    content = await file.read()
    
    # Check file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size too large. Maximum size is 10MB."
        )
    
    # Save file
    with open(file_path, "wb") as buffer:
        buffer.write(content)
    
    return str(file_path)

@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile."""
    return current_user

@router.put("/profile", response_model=UserResponse)
async def update_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user's profile."""
    try:
        update_data = user_update.dict(exclude_unset=True)
        if not update_data:
            return current_user
        
        # Update user fields
        for field, value in update_data.items():
            setattr(current_user, field, value)
        
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

@router.get("/", response_model=list[UserResponse])
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
            return users
        
    except Exception as e:
        log_error(f"List users error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch users"
        )

@router.get("/{user_id}", response_model=UserResponse)
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user
        
    except Exception as e:
        log_error(f"Get user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user"
        )

@router.post("/upload-profile-image", response_model=FileUploadResponse)
async def upload_profile_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload profile image."""
    try:
        file_path = await save_uploaded_file(file, current_user.id, "profile")
        
        # Update user record (profile photos are auto-approved)
        current_user.profile_image = file_path
        current_user.profile_image_status = DocumentStatus.APPROVED
        await db.commit()
        await db.refresh(current_user)
        
        log_info(f"Profile image uploaded for user: {current_user.email}")
        return FileUploadResponse(
            filename=file.filename,
            file_path=file_path,
            file_size=len(await file.read()),
            content_type=file.content_type or "application/octet-stream"
        )
        
    except Exception as e:
        log_error(f"Profile image upload error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload profile image"
        )

@router.post("/upload-aadhaar-front", response_model=FileUploadResponse)
async def upload_aadhaar_front(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload Aadhaar front image."""
    try:
        file_path = await save_uploaded_file(file, current_user.id, "aadhaar_front")
        
        # Update user record
        current_user.aadhaar_front = file_path
        current_user.aadhaar_front_status = DocumentStatus.PENDING
        await db.commit()
        await db.refresh(current_user)
        
        log_info(f"Aadhaar front uploaded for user: {current_user.email}")
        return FileUploadResponse(
            filename=file.filename,
            file_path=file_path,
            file_size=len(await file.read()),
            content_type=file.content_type or "application/octet-stream"
        )
        
    except Exception as e:
        log_error(f"Aadhaar front upload error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload Aadhaar front"
        )

@router.post("/upload-aadhaar-back", response_model=FileUploadResponse)
async def upload_aadhaar_back(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload Aadhaar back image."""
    try:
        file_path = await save_uploaded_file(file, current_user.id, "aadhaar_back")
        
        # Update user record
        current_user.aadhaar_back = file_path
        current_user.aadhaar_back_status = DocumentStatus.PENDING
        await db.commit()
        await db.refresh(current_user)
        
        log_info(f"Aadhaar back uploaded for user: {current_user.email}")
        return FileUploadResponse(
            filename=file.filename,
            file_path=file_path,
            file_size=len(await file.read()),
            content_type=file.content_type or "application/octet-stream"
        )
        
    except Exception as e:
        log_error(f"Aadhaar back upload error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload Aadhaar back"
        )

@router.post("/upload-pan", response_model=FileUploadResponse)
async def upload_pan(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload PAN image."""
    try:
        file_path = await save_uploaded_file(file, current_user.id, "pan")
        
        # Update user record
        current_user.pan_image = file_path
        current_user.pan_image_status = DocumentStatus.PENDING
        await db.commit()
        await db.refresh(current_user)
        
        log_info(f"PAN uploaded for user: {current_user.email}")
        return FileUploadResponse(
            filename=file.filename,
            file_path=file_path,
            file_size=len(await file.read()),
            content_type=file.content_type or "application/octet-stream"
        )
        
    except Exception as e:
        log_error(f"PAN upload error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload PAN"
        )

# Employee Management Endpoints for Users
@router.get("/my-employee-details", response_model=Optional[EmployeeDetailsResponse])
async def get_my_employee_details(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's employee details (read-only access)."""
    try:
        # Security: Ensure user is active
        if not current_user.is_active:
            log_error(f"Inactive user {current_user.email} attempted to access employee details")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )
        
        log_info(f"User {current_user.email} (ID: {current_user.id}) accessing employee details")
        
        result = await db.execute(
            select(EmployeeDetails)
            .options(
                selectinload(EmployeeDetails.user),
                selectinload(EmployeeDetails.manager)
            )
            .where(EmployeeDetails.user_id == current_user.id)
        )
        employee_details = result.scalar_one_or_none()
        
        # Only return employee details if they exist and are active
        if employee_details and not employee_details.is_active:
            employee_details = None
        
        # Log access for audit
        log_info(f"User {current_user.email} accessed their employee details")
        return employee_details
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Get my employee details error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch employee details"
        )

@router.get("/my-employment-history", response_model=List[EmploymentHistoryResponse])
async def get_my_employment_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's employment history (read-only access)."""
    try:
        # Security: Ensure user is active
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )
        
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
        
        # Log access for audit
        log_info(f"User {current_user.email} accessed their employment history")
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Get my employment history error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch employment history"
        )

@router.get("/my-employee-summary", response_model=EmployeeSummary)
async def get_my_employee_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's comprehensive employee summary (read-only access)."""
    try:
        # Security: Ensure user is active
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )
        
        # Get employee details with security check
        details_result = await db.execute(
            select(EmployeeDetails)
            .options(
                selectinload(EmployeeDetails.user),
                selectinload(EmployeeDetails.manager)
            )
            .where(and_(
                EmployeeDetails.user_id == current_user.id,
                EmployeeDetails.is_active == True
            ))
        )
        employee_details = details_result.scalar_one_or_none()
        
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
        
        return EmployeeSummary(
            user=current_user,
            employee_details=employee_details,
            current_position=current_position,
            recent_tracking=[],
            total_work_days=total_work_days,
            average_hours_per_day=average_hours_per_day
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Get my employee summary error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch employee summary"
        )


@router.get("/my-department-colleagues")
async def get_my_department_colleagues(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get colleagues from the same department."""
    try:
        # Security: Ensure user is active
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )
        # Get current user's department
        user_details_result = await db.execute(
            select(EmployeeDetails).where(EmployeeDetails.user_id == current_user.id)
        )
        user_details = user_details_result.scalar_one_or_none()
        
        if not user_details or not user_details.department:
            return {"colleagues": [], "department": None}
        
        # Get colleagues from same department
        colleagues_result = await db.execute(
            select(User)
            .join(EmployeeDetails)
            .where(
                and_(
                    EmployeeDetails.department == user_details.department,
                    User.id != current_user.id,
                    User.is_active == True
                )
            )
            .options(selectinload(User.employee_details))
        )
        colleagues = colleagues_result.scalars().all()
        
        return {
            "department": user_details.department,
            "colleagues": [
                {
                    "id": colleague.id,
                    "name": colleague.name,
                    "email": colleague.email,
                    "designation": colleague.designation,
                    "employee_details": getattr(colleague, 'employee_details', None)
                }
                for colleague in colleagues
            ]
        }
        
    except Exception as e:
        log_error(f"Get department colleagues error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch department colleagues"
        )

@router.get("/my-manager")
async def get_my_manager(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's manager information."""
    try:
        # Security: Ensure user is active
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )
        # Get current user's manager from employee details
        user_details_result = await db.execute(
            select(EmployeeDetails)
            .options(selectinload(EmployeeDetails.manager))
            .where(EmployeeDetails.user_id == current_user.id)
        )
        user_details = user_details_result.scalar_one_or_none()
        
        if not user_details or not user_details.manager_id:
            return {"manager": None}
        
        # Get manager details
        manager_result = await db.execute(
            select(User).where(User.id == user_details.manager_id)
        )
        manager = manager_result.scalar_one_or_none()
        
        if not manager:
            return {"manager": None}
        
        return {
            "manager": {
                "id": manager.id,
                "name": manager.name,
                "email": manager.email,
                "designation": manager.designation,
                "phone": manager.phone
            }
        }
        
    except Exception as e:
        log_error(f"Get my manager error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch manager information"
        )
