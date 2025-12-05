from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, text, update
from fastapi import UploadFile, File
from pathlib import Path
import uuid
from sqlalchemy.orm import selectinload
from datetime import datetime, date
from typing import List, Dict, Any
from app.database import get_db
from app.models import User, Leave, Holiday, LeaveStatus, UserRole, DocumentStatus, EmploymentHistory
from app.schema import (
    UserResponse, LeaveResponse, HolidayResponse, TrackerResponse, UserCreate,
    EmploymentHistoryResponse, EmployeeSummary, EnhancedTrackerResponse,
    EmployeeDetailsCreate, EmployeeDetailsUpdate, EmploymentHistoryCreate, AdminUserUpdate
)
from app.auth import get_current_admin_user, get_password_hash
from app.logger import log_info, log_error
from app.storage import storage

router = APIRouter(prefix="/admin", tags=["admin"])

async def safe_get_employee_details(db: AsyncSession, user_id: int):
    """With merged model, return the User record itself."""
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    except Exception as e:
        log_error(f"Error fetching user {user_id}: {str(e)}")
        return None

# Admin can upload documents for any user
@router.post("/users/{user_id}/upload-profile-image")
async def admin_upload_profile_image(
    user_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        target_user = result.scalar_one_or_none()
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Delete old file if exists
        if target_user.profile_image:
            await storage.delete_file(target_user.profile_image)
        
        # Upload new file using storage service
        file_path = await storage.upload_file(file, user_id, "profile")
        target_user.profile_image = file_path
        target_user.profile_image_status = DocumentStatus.APPROVED
        await db.commit()
        
        return {
            "file_path": file_path,
            "file_url": storage.get_file_url(file_path)
        }
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Admin upload profile image error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload profile image")

@router.post("/users/{user_id}/upload-aadhaar-front")
async def admin_upload_aadhaar_front(
    user_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        target_user = result.scalar_one_or_none()
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Delete old file if exists
        if target_user.aadhaar_front:
            await storage.delete_file(target_user.aadhaar_front)
        
        # Upload new file using storage service
        file_path = await storage.upload_file(file, user_id, "aadhaar_front")
        target_user.aadhaar_front = file_path
        target_user.aadhaar_front_status = DocumentStatus.APPROVED
        await db.commit()
        
        return {
            "file_path": file_path,
            "file_url": storage.get_file_url(file_path)
        }
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Admin upload aadhaar front error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload Aadhaar front")

@router.post("/users/{user_id}/upload-aadhaar-back")
async def admin_upload_aadhaar_back(
    user_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        target_user = result.scalar_one_or_none()
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Delete old file if exists
        if target_user.aadhaar_back:
            await storage.delete_file(target_user.aadhaar_back)
        
        # Upload new file using storage service
        file_path = await storage.upload_file(file, user_id, "aadhaar_back")
        target_user.aadhaar_back = file_path
        target_user.aadhaar_back_status = DocumentStatus.APPROVED
        await db.commit()
        
        return {
            "file_path": file_path,
            "file_url": storage.get_file_url(file_path)
        }
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Admin upload aadhaar back error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload Aadhaar back")

@router.post("/users/{user_id}/upload-pan")
async def admin_upload_pan(
    user_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        target_user = result.scalar_one_or_none()
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Delete old file if exists
        if target_user.pan_image:
            await storage.delete_file(target_user.pan_image)
        
        # Upload new file using storage service
        file_path = await storage.upload_file(file, user_id, "pan")
        target_user.pan_image = file_path
        target_user.pan_image_status = DocumentStatus.APPROVED
        await db.commit()
        
        return {
            "file_path": file_path,
            "file_url": storage.get_file_url(file_path)
        }
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Admin upload pan error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload PAN")
# Document approval endpoints (super admin only)
@router.put("/users/{user_id}/documents/{doc_type}/approve")
async def approve_document(
    user_id: int,
    doc_type: str,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        doc_type = doc_type.lower()
        if doc_type == "profile":
            user.profile_image_status = DocumentStatus.APPROVED
        elif doc_type == "aadhaar_front":
            user.aadhaar_front_status = DocumentStatus.APPROVED
        elif doc_type == "aadhaar_back":
            user.aadhaar_back_status = DocumentStatus.APPROVED
        elif doc_type == "pan":
            user.pan_image_status = DocumentStatus.APPROVED
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid document type")

        await db.commit()
        return {"status": "approved"}
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Approve document error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to approve document")

@router.put("/users/{user_id}/documents/{doc_type}/reject")
async def reject_document(
    user_id: int,
    doc_type: str,
    reason: str | None = None,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        doc_type = doc_type.lower()
        if doc_type == "profile":
            user.profile_image_status = DocumentStatus.REJECTED
        elif doc_type == "aadhaar_front":
            user.aadhaar_front_status = DocumentStatus.REJECTED
        elif doc_type == "aadhaar_back":
            user.aadhaar_back_status = DocumentStatus.REJECTED
        elif doc_type == "pan":
            user.pan_image_status = DocumentStatus.REJECTED
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid document type")

        await db.commit()
        return {"status": "rejected", "reason": reason}
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Reject document error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to reject document")

@router.get("/dashboard")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard statistics (admin only)."""
    try:
        from app.database import monitor_query
        
        async with monitor_query("dashboard_stats"):
            today = datetime.now().date()
            
            # Initialize default values
            total_users = 0
            active_users = 0
            pending_leaves = 0
            upcoming_holidays = 0
            
            # Get total users (safe)
            try:
                total_users_result = await db.execute(select(func.count(User.id)))
                total_users = total_users_result.scalar() or 0
            except Exception as e:
                log_error(f"Error getting total users: {str(e)}")
            
            # Get active users today (tracking disabled)
            active_users = 0
            
            # Get pending leaves (safe)
            try:
                pending_leaves_result = await db.execute(
                    select(func.count(Leave.id)).where(Leave.status == LeaveStatus.PENDING)
                )
                pending_leaves = pending_leaves_result.scalar() or 0
            except Exception as e:
                log_error(f"Error getting pending leaves: {str(e)}")
            
            # Get upcoming holidays (safe)
            try:
                upcoming_holidays_result = await db.execute(
                    select(func.count(Holiday.id)).where(
                        and_(
                            func.date(Holiday.date) >= today,
                            Holiday.is_active == True
                        )
                    )
                )
                upcoming_holidays = upcoming_holidays_result.scalar() or 0
            except Exception as e:
                log_error(f"Error getting upcoming holidays: {str(e)}")
            
            return {
                "total_users": total_users,
                "active_users_today": active_users,
                "pending_leaves": pending_leaves,
                "upcoming_holidays": upcoming_holidays
            }
        
    except Exception as e:
        log_error(f"Dashboard stats error: {str(e)}")
        # Return default values instead of throwing error
        return {
            "total_users": 0,
            "active_users_today": 0,
            "pending_leaves": 0,
            "upcoming_holidays": 0
        }

@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    role: str = "user",
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new user with specified role (admin only)."""
    try:
        # Validate role
        if role not in [UserRole.USER, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role. Must be 'user' or 'admin'"
            )
        
        # Check if user already exists
        existing_user = await db.execute(select(User).where(User.email == user_data.email))
        if existing_user.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            name=user_data.name,
            phone=user_data.phone,
            designation=user_data.designation,
            joining_date=user_data.joining_date,
            wifi_user_id=user_data.wifi_user_id,
            role=role
        )
        
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        
        log_info(f"New user created: {user_data.email} with role: {role} by admin: {current_user.email}")
        return db_user
        
    except Exception as e:
        log_error(f"Create user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: AdminUserUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user information (admin only)."""
    log_info(f"PUT /admin/users/{user_id} called by {current_user.email}")
    try:
        # Get user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Validate role if provided
        if user_data.role is not None:
            log_info(f"Role validation - received role: {user_data.role} (type: {type(user_data.role)})")
            # Convert string role to UserRole enum if needed
            if isinstance(user_data.role, str):
                try:
                    user_data.role = UserRole(user_data.role)
                    log_info(f"Converted string role to enum: {user_data.role}")
                except ValueError:
                    log_error(f"Invalid role string: {user_data.role}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid role value: {user_data.role}. Must be 'user' or 'admin'"
                    )
            
            if user_data.role not in [UserRole.USER, UserRole.ADMIN]:
                log_error(f"Role not in allowed values: {user_data.role}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid role. Must be 'user' or 'admin'"
                )
            
            log_info(f"Role validation passed: {user_data.role}")
        
        # Check email uniqueness if email is being updated
        if user_data.email is not None and user_data.email != user.email:
            existing_user = await db.execute(select(User).where(User.email == user_data.email))
            if existing_user.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        
        # Update user fields using Pydantic model
        update_data = user_data.model_dump(exclude_unset=True)
        log_info(f"Update data for user {user_id}: {update_data}")
        
        # Update basic fields
        if 'name' in update_data:
            user.name = update_data['name']
            log_info(f"Updated name to: {update_data['name']}")
        if 'email' in update_data:
            user.email = update_data['email']
            log_info(f"Updated email to: {update_data['email']}")
        if 'phone' in update_data:
            user.phone = update_data['phone']
            log_info(f"Updated phone to: {update_data['phone']}")
        if 'designation' in update_data:
            user.designation = update_data['designation']
            log_info(f"Updated designation to: {update_data['designation']}")
        if 'joining_date' in update_data:
            user.joining_date = update_data['joining_date']
            log_info(f"Updated joining_date to: {update_data['joining_date']}")
        if 'wifi_user_id' in update_data:
            user.wifi_user_id = update_data['wifi_user_id']
            log_info(f"Updated wifi_user_id to: {update_data['wifi_user_id']}")
        if 'role' in update_data:
            user.role = update_data['role']
            log_info(f"Updated role to: {update_data['role']}")
        
        # Update document fields and set status to pending when updated
        if 'profile_image' in update_data:
            user.profile_image = update_data['profile_image']
            user.profile_image_status = DocumentStatus.PENDING
            log_info(f"Updated profile_image to: {update_data['profile_image']}")
        if 'aadhaar_front' in update_data:
            user.aadhaar_front = update_data['aadhaar_front']
            user.aadhaar_front_status = DocumentStatus.PENDING
            log_info(f"Updated aadhaar_front to: {update_data['aadhaar_front']}")
        if 'aadhaar_back' in update_data:
            user.aadhaar_back = update_data['aadhaar_back']
            user.aadhaar_back_status = DocumentStatus.PENDING
            log_info(f"Updated aadhaar_back to: {update_data['aadhaar_back']}")
        if 'pan_image' in update_data:
            user.pan_image = update_data['pan_image']
            user.pan_image_status = DocumentStatus.PENDING
            log_info(f"Updated pan_image to: {update_data['pan_image']}")

        log_info(f"About to commit changes for user {user_id}")
        await db.commit()
        log_info(f"Changes committed for user {user_id}")
        await db.refresh(user)
        log_info(f"User {user_id} refreshed from database")
        
        log_info(f"User {user_id} updated by admin {current_user.email}")
        return user
        
    except Exception as e:
        log_error(f"Update user error: {str(e)}")
        import traceback
        log_error(f"Update user traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )

@router.patch("/users/{user_id}", response_model=UserResponse)
async def patch_user(
    user_id: int,
    user_data: AdminUserUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Partially update user information (admin only)."""
    log_info(f"PATCH /admin/users/{user_id} called by {current_user.email}")
    try:
        # Get user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Validate role if provided
        if user_data.role is not None:
            log_info(f"Role validation - received role: {user_data.role} (type: {type(user_data.role)})")
            # Convert string role to UserRole enum if needed
            if isinstance(user_data.role, str):
                try:
                    user_data.role = UserRole(user_data.role)
                    log_info(f"Converted string role to enum: {user_data.role}")
                except ValueError:
                    log_error(f"Invalid role string: {user_data.role}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid role value: {user_data.role}. Must be 'user' or 'admin'"
                    )
            
            if user_data.role not in [UserRole.USER, UserRole.ADMIN]:
                log_error(f"Role not in allowed values: {user_data.role}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid role. Must be 'user' or 'admin'"
                )
            
            log_info(f"Role validation passed: {user_data.role}")
        
        # Check email uniqueness if email is being updated
        if user_data.email is not None and user_data.email != user.email:
            existing_user = await db.execute(select(User).where(User.email == user_data.email))
            if existing_user.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        
        # Update user fields using Pydantic model (PATCH behavior - only update provided fields)
        update_data = user_data.model_dump(exclude_unset=True)
        log_info(f"PATCH update data for user {user_id}: {update_data}")
        
        # Update basic fields
        if 'name' in update_data:
            user.name = update_data['name']
            log_info(f"Updated name to: {update_data['name']}")
        if 'email' in update_data:
            user.email = update_data['email']
            log_info(f"Updated email to: {update_data['email']}")
        if 'phone' in update_data:
            user.phone = update_data['phone']
            log_info(f"Updated phone to: {update_data['phone']}")
        if 'designation' in update_data:
            user.designation = update_data['designation']
            log_info(f"Updated designation to: {update_data['designation']}")
        if 'joining_date' in update_data:
            user.joining_date = update_data['joining_date']
            log_info(f"Updated joining_date to: {update_data['joining_date']}")
        if 'wifi_user_id' in update_data:
            user.wifi_user_id = update_data['wifi_user_id']
            log_info(f"Updated wifi_user_id to: {update_data['wifi_user_id']}")
        if 'role' in update_data:
            user.role = update_data['role']
            log_info(f"Updated role to: {update_data['role']}")
        
        # Update document fields and set status to pending when updated
        if 'profile_image' in update_data:
            user.profile_image = update_data['profile_image']
            user.profile_image_status = DocumentStatus.PENDING
            log_info(f"Updated profile_image to: {update_data['profile_image']}")
        if 'aadhaar_front' in update_data:
            user.aadhaar_front = update_data['aadhaar_front']
            user.aadhaar_front_status = DocumentStatus.PENDING
            log_info(f"Updated aadhaar_front to: {update_data['aadhaar_front']}")
        if 'aadhaar_back' in update_data:
            user.aadhaar_back = update_data['aadhaar_back']
            user.aadhaar_back_status = DocumentStatus.PENDING
            log_info(f"Updated aadhaar_back to: {update_data['aadhaar_back']}")
        if 'pan_image' in update_data:
            user.pan_image = update_data['pan_image']
            user.pan_image_status = DocumentStatus.PENDING
            log_info(f"Updated pan_image to: {update_data['pan_image']}")

        log_info(f"About to commit PATCH changes for user {user_id}")
        await db.commit()
        log_info(f"PATCH changes committed for user {user_id}")
        await db.refresh(user)
        log_info(f"User {user_id} refreshed from database")
        
        log_info(f"User {user_id} patched by admin {current_user.email}")
        return user
        
    except Exception as e:
        log_error(f"PATCH user error: {str(e)}")
        import traceback
        log_error(f"PATCH user traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to patch user: {str(e)}"
        )

@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    offset: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all users with pagination (admin only)."""
    try:
        result = await db.execute(
            select(User)
            .offset(offset)
            .limit(limit)
            .order_by(User.created_at.desc())
        )
        users = result.scalars().all()
        return users
        
    except Exception as e:
        log_error(f"Get all users error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch users"
        )

@router.get("/leaves", response_model=List[LeaveResponse])
async def get_all_leaves(
    offset: int = 0,
    limit: int = 10,
    status_filter: str = None,
    active_users_only: bool = True,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all leave applications with optional status filter (admin only).
    By default, only shows leaves from active users."""
    try:
        query = select(Leave).options(selectinload(Leave.user))
        
        # Filter by active users by default
        if active_users_only:
            # Get active user IDs
            active_users_query = select(User.id).where(User.is_active == True)
            query = query.where(Leave.user_id.in_(active_users_query))
        
        if status_filter:
            query = query.where(Leave.status == status_filter)
        
        result = await db.execute(
            query
            .offset(offset)
            .limit(limit)
            .order_by(Leave.created_at.desc())
        )
        leaves = result.scalars().all()
        return leaves
        
    except Exception as e:
        log_error(f"Get all leaves error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch leaves"
        )


@router.get("/user/{user_id}/summary")
async def get_user_summary(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive summary for a specific user (admin only)."""
    try:
        # Get user info
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get user's leaves
        leaves_result = await db.execute(
            select(Leave).where(Leave.user_id == user_id).order_by(Leave.created_at.desc())
        )
        leaves = leaves_result.scalars().all()
        
        # Tracking disabled
        tracking = []
        
        # Calculate stats
        total_leaves = len(leaves)
        approved_leaves = len([l for l in leaves if l.status == LeaveStatus.APPROVED])
        pending_leaves = len([l for l in leaves if l.status == LeaveStatus.PENDING])
        rejected_leaves = len([l for l in leaves if l.status == LeaveStatus.REJECTED])
        
        return {
            "user": user,
            "leaves": {
                "total": total_leaves,
                "approved": approved_leaves,
                "pending": pending_leaves,
                "rejected": rejected_leaves,
                "recent": leaves[:5]
            },
            "tracking": {
                "recent_records": tracking[:10],
                "total_records": len(tracking)
            }
        }
        
    except Exception as e:
        log_error(f"Get user summary error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user summary"
        )

@router.put("/leaves/{leave_id}/approve")
async def approve_leave(
    leave_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Approve a leave application (admin only)."""
    try:
        # Get leave application
        result = await db.execute(
            select(Leave)
            .options(selectinload(Leave.user))
            .where(Leave.id == leave_id)
        )
        leave = result.scalar_one_or_none()
        
        if not leave:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Leave application not found"
            )
        
        if leave.status != LeaveStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Leave application is not pending"
            )
        
        # Approve leave
        leave.status = LeaveStatus.APPROVED
        await db.commit()
        await db.refresh(leave)
        
        log_info(f"Leave {leave_id} approved by admin {current_user.email}")
        return {"message": "Leave approved successfully", "leave": leave}
        
    except Exception as e:
        log_error(f"Approve leave error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve leave"
        )

@router.put("/leaves/{leave_id}/reject")
async def reject_leave(
    leave_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Reject a leave application (admin only)."""
    try:
        # Get leave application
        result = await db.execute(
            select(Leave)
            .options(selectinload(Leave.user))
            .where(Leave.id == leave_id)
        )
        leave = result.scalar_one_or_none()
        
        if not leave:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Leave application not found"
            )
        
        if leave.status != LeaveStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Leave application is not pending"
            )
        
        # Reject leave
        leave.status = LeaveStatus.REJECTED
        await db.commit()
        await db.refresh(leave)
        
        log_info(f"Leave {leave_id} rejected by admin {current_user.email}")
        return {"message": "Leave rejected successfully", "leave": leave}
        
    except Exception as e:
        log_error(f"Reject leave error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject leave"
        )

@router.get("/leaves/pending", response_model=List[LeaveResponse])
async def get_pending_leaves(
    offset: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all pending leave applications (admin only)."""
    try:
        result = await db.execute(
            select(Leave)
            .options(selectinload(Leave.user))
            .where(Leave.status == LeaveStatus.PENDING)
            .offset(offset)
            .limit(limit)
            .order_by(Leave.created_at.asc())
        )
        leaves = result.scalars().all()
        return leaves
        
    except Exception as e:
        log_error(f"Get pending leaves error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch pending leaves"
        )

@router.post("/holidays/bulk", response_model=List[HolidayResponse])
async def create_bulk_holidays(
    holidays: List[dict],
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create multiple holidays at once (admin only)."""
    try:
        created_holidays = []
        
        for holiday_data in holidays:
            try:
                # Convert date string to datetime if needed
                date_value = holiday_data["date"]
                if isinstance(date_value, str):
                    from datetime import datetime
                    
                    # Try parsing with different formats
                    date_formats = [
                        '%Y-%m-%d',      # YYYY-MM-DD
                        '%m/%d/%Y',      # MM/DD/YYYY
                        '%d/%m/%Y',      # DD/MM/YYYY
                        '%m-%d-%Y',      # MM-DD-YYYY
                        '%d-%m-%Y',      # DD-MM-YYYY
                        '%Y/%m/%d',      # YYYY/MM/DD
                        '%d.%m.%Y',      # DD.MM.YYYY
                        '%m.%d.%Y',      # MM.DD.YYYY
                        '%Y.%m.%d',      # YYYY.MM.DD
                    ]
                    
                    parsed_date = None
                    for fmt in date_formats:
                        try:
                            parsed_date = datetime.strptime(date_value.strip(), fmt)
                            break
                        except ValueError:
                            continue
                    
                    if not parsed_date:
                        # Try parsing with different separators and order combinations
                        separators = ['-', '/', '.', ' ']
                        for sep in separators:
                            if sep in date_value:
                                parts = date_value.split(sep)
                                if len(parts) == 3:
                                    # Try different order combinations
                                    combinations = [
                                        (parts[0], parts[1], parts[2]),  # Original order
                                        (parts[2], parts[0], parts[1]),  # YYYY-MM-DD
                                        (parts[2], parts[1], parts[0]),  # YYYY-DD-MM
                                    ]
                                    
                                    for year, month, day in combinations:
                                        try:
                                            # Ensure proper padding
                                            year = year.zfill(4)
                                            month = month.zfill(2)
                                            day = day.zfill(2)
                                            
                                            # Validate year range
                                            if 1900 <= int(year) <= 2100:
                                                parsed_date = datetime.strptime(f"{year}-{month}-{day}", '%Y-%m-%d')
                                                break
                                        except ValueError:
                                            continue
                                    if parsed_date:
                                        break
                    
                    if not parsed_date:
                        log_error(f"Invalid date format: {date_value}")
                        continue
                    
                    holiday_data["date"] = parsed_date
                
                # Check if holiday already exists
                existing_holiday = await db.execute(
                    select(Holiday).where(Holiday.date == holiday_data["date"])
                )
                if existing_holiday.scalar_one_or_none():
                    log_info(f"Holiday already exists for date {holiday_data['date']}, skipping")
                    continue
                
                # Create holiday
                db_holiday = Holiday(
                    date=holiday_data["date"],
                    title=holiday_data["title"],
                    description=holiday_data.get("description"),
                    is_active=holiday_data.get("is_active", True)
                )
                db.add(db_holiday)
                created_holidays.append(db_holiday)
                
            except Exception as e:
                log_error(f"Error processing holiday {holiday_data}: {str(e)}")
                continue
        
        await db.commit()
        
        # Refresh all created holidays
        for holiday in created_holidays:
            await db.refresh(holiday)
        
        log_info(f"Bulk holidays created by admin {current_user.email}: {len(created_holidays)} holidays")
        return created_holidays
        
    except Exception as e:
        log_error(f"Create bulk holidays error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create bulk holidays"
        )


@router.get("/holidays", response_model=List[HolidayResponse])
async def get_all_holidays_admin(
    offset: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all holidays with admin privileges (admin only)."""
    try:
        result = await db.execute(
            select(Holiday)
            .offset(offset)
            .limit(limit)
            .order_by(Holiday.date.asc())
        )
        holidays = result.scalars().all()
        return holidays
        
    except Exception as e:
        log_error(f"Get all holidays admin error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch holidays"
        )

@router.put("/users/{user_id}/activate")
async def activate_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Activate a user account (admin only)."""
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.is_active = True
        await db.commit()
        await db.refresh(user)
        
        log_info(f"User {user_id} activated by admin {current_user.email}")
        return {"message": "User activated successfully", "user": user}
        
    except Exception as e:
        log_error(f"Activate user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate user"
        )

@router.put("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Deactivate a user account (admin only)."""
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate your own account"
            )
        
        user.is_active = False
        await db.commit()
        await db.refresh(user)
        
        log_info(f"User {user_id} deactivated by admin {current_user.email}")
        return {"message": "User deactivated successfully", "user": user}
        
    except Exception as e:
        log_error(f"Deactivate user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user"
        )

@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    new_role: str,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user role (admin only)."""
    try:
        if new_role not in [UserRole.USER, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role. Must be 'user' or 'admin'"
            )
        
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change your own role"
            )
        
        user.role = new_role
        await db.commit()
        await db.refresh(user)
        
        log_info(f"User {user_id} role updated to {new_role} by admin {current_user.email}")
        return {"message": f"User role updated to {new_role}", "user": user}
        
    except Exception as e:
        log_error(f"Update user role error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user role"
        )

@router.put("/users/{user_id}/toggle-status")
async def toggle_user_status(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Toggle user active status (admin only)."""
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change your own status"
            )

        # Toggle user status
        user.is_active = not user.is_active

        # No separate employee_details to sync after merge

        await db.commit()
        await db.refresh(user)
        
        status_text = "activated" if user.is_active else "deactivated"
        log_info(f"User {user_id} {status_text} by admin {current_user.email}")
        return {"message": f"User {status_text} successfully", "user": user}
        
    except Exception as e:
        await db.rollback()
        log_error(f"Toggle user status error: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle user status: {str(e) or 'internal error'}"
        )

@router.patch("/users/{user_id}/toggle-status")
async def toggle_user_status_patch(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """PATCH alias for toggling user active status (admin only)."""
    # Delegate to the PUT handler to keep logic in one place
    return await toggle_user_status(user_id, current_user, db)

@router.put("/users/{user_id}/promote")
async def promote_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Promote user to admin (admin only)."""
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.role == UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already an admin"
            )
        
        user.role = UserRole.ADMIN
        await db.commit()
        await db.refresh(user)
        
        log_info(f"User {user_id} promoted to admin by {current_user.email}")
        return {"message": "User promoted to admin successfully", "user": user}
        
    except Exception as e:
        log_error(f"Promote user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to promote user"
        )

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete user account (admin only)."""
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if trying to delete own account
        if user.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        # Delete related records first
        from app.models import EmploymentHistory
        
        # Delete employment history
        employment_history_result = await db.execute(
            select(EmploymentHistory).where(EmploymentHistory.user_id == user_id)
        )
        employment_history_records = employment_history_result.scalars().all()
        for history in employment_history_records:
            await db.delete(history)
        
        # Delete user leaves
        from app.models import Leave
        leaves_result = await db.execute(
            select(Leave).where(Leave.user_id == user_id)
        )
        leaves = leaves_result.scalars().all()
        for leave in leaves:
            await db.delete(leave)
        
        # Update any users that reference this user as manager/reviewer/initiator
        await db.execute(
            update(User)
            .where(User.manager_id == user_id)
            .values(manager_id=None)
        )
        await db.execute(
            update(User)
            .where(User.probation_reviewer_id == user_id)
            .values(probation_reviewer_id=None)
        )
        await db.execute(
            update(User)
            .where(User.termination_initiated_by == user_id)
            .values(termination_initiated_by=None)
        )
        
        # Set manager_id to NULL for employment history where this user is the manager
        await db.execute(
            update(EmploymentHistory)
            .where(EmploymentHistory.manager_id == user_id)
            .values(manager_id=None)
        )
        
        # Delete user
        await db.delete(user)
        await db.commit()
        
        log_info(f"User {user_id} deleted by admin {current_user.email}")
        return {"message": "User deleted successfully"}
        
    except Exception as e:
        log_error(f"Delete user error: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )

@router.get("/reports/leaves")
async def get_leaves_report(
    start_date: str = None,
    end_date: str = None,
    status_filter: str = None,
    active_users_only: bool = True,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive leaves report grouped by user (admin only).
    By default, only shows leaves from active users."""
    try:
        from collections import defaultdict
        
        # Get active users only by default
        if active_users_only:
            users_result = await db.execute(select(User).where(User.is_active == True))
        else:
            users_result = await db.execute(select(User))
        all_users = users_result.scalars().all()
        
        # Build query for leaves - filter by active users by default
        query = select(Leave).options(selectinload(Leave.user))
        
        # Filter leaves to only include those from active users
        if active_users_only:
            active_users_query = select(User.id).where(User.is_active == True)
            query = query.where(Leave.user_id.in_(active_users_query))
        
        if start_date and end_date:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            query = query.where(
                and_(
                    Leave.start_date >= start,
                    Leave.end_date <= end
                )
            )
        
        if status_filter:
            query = query.where(Leave.status == status_filter)
        
        result = await db.execute(query)
        leaves = result.scalars().all()
        
        # Calculate leave totals per user (count and total days)
        user_leave_data = defaultdict(lambda: {
            "total_leaves": 0,
            "approved_leaves": 0,
            "pending_leaves": 0,
            "rejected_leaves": 0,
            "total_days_taken": 0.0,
            "approved_days": 0.0,
            "pending_days": 0.0,
            "rejected_days": 0.0
        })
        
        for leave in leaves:
            user_id = leave.user_id
            leave_days = float(leave.total_days)
            
            user_leave_data[user_id]["total_leaves"] += 1
            user_leave_data[user_id]["total_days_taken"] += leave_days
            
            if leave.status == LeaveStatus.APPROVED:
                user_leave_data[user_id]["approved_leaves"] += 1
                user_leave_data[user_id]["approved_days"] += leave_days
            elif leave.status == LeaveStatus.PENDING:
                user_leave_data[user_id]["pending_leaves"] += 1
                user_leave_data[user_id]["pending_days"] += leave_days
            elif leave.status == LeaveStatus.REJECTED:
                user_leave_data[user_id]["rejected_leaves"] += 1
                user_leave_data[user_id]["rejected_days"] += leave_days
        
        # Build response with leave summaries
        report_data = []
        
        # Get current date for calculations
        from datetime import datetime as dt
        current_date = dt.now().date()
        
        for user in all_users:
            user_data = user_leave_data.get(user.id, {
                "total_leaves": 0,
                "approved_leaves": 0,
                "pending_leaves": 0,
                "rejected_leaves": 0,
                "total_days_taken": 0.0,
                "approved_days": 0.0,
                "pending_days": 0.0,
                "rejected_days": 0.0
            })
            
            # Monthly leave policy: Everyone gets 1 leave per month (current month's allocation)
            # No accumulation - just the current month's leave allocation
            if user.joining_date:
                join_date = user.joining_date
                
                # Calculate total months from joining date to current date
                # Calculate years difference
                years_diff = current_date.year - join_date.year
                
                # Calculate months difference
                months_diff = current_date.month - join_date.month
                
                # Total months
                total_months = years_diff * 12 + months_diff
                
                # Add 1 more month if we're past the joining day in the current month
                if current_date.day >= join_date.day and total_months >= 0:
                    total_months += 1
                elif total_months < 0:
                    # If joining date is in the future, set to 0
                    total_months = 0
                
                # Monthly leave allocation: Everyone gets 1 leave per month
                # No accumulation - just show current month's allocation
                allocated_leaves = 1
                
                log_info(f"User {user.name} ({user.email}): Joined {join_date}, Current {current_date}, Total Months: {total_months}, Allocated Leaves: {allocated_leaves}")
            else:
                # If no joining date, assume 1 leave (current month)
                allocated_leaves = 1
                log_info(f"User {user.name} ({user.email}): No joining date set, defaulting to 1 leave")
            
            # Calculate remaining leave (Available - Approved)
            remaining_leaves = allocated_leaves - user_data["approved_leaves"]
            
            # Calculate total leaves taken (all statuses)
            total_leaves_taken = user_data["approved_leaves"] + user_data["pending_leaves"] + user_data["rejected_leaves"]
            
            report_data.append({
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email
                },
                "total_leaves": total_leaves_taken,
                "approved_leaves": user_data["approved_leaves"],
                "pending_leaves": user_data["pending_leaves"],
                "rejected_leaves": user_data["rejected_leaves"],
                "total_days_taken": round(user_data["total_days_taken"], 1),
                "approved_days": round(user_data["approved_days"], 1),
                "pending_days": round(user_data["pending_days"], 1),
                "rejected_days": round(user_data["rejected_days"], 1),
                "remaining_leaves": max(0, remaining_leaves),  # Don't show negative
                "allocated_leaves": allocated_leaves
            })
        
        # Sort by total leaves (descending)
        report_data.sort(key=lambda x: x["total_leaves"], reverse=True)
        
        # Calculate overall statistics
        total_users = len(all_users)
        total_leaves = len(leaves)
        approved_leaves = len([l for l in leaves if l.status == LeaveStatus.APPROVED])
        pending_leaves = len([l for l in leaves if l.status == LeaveStatus.PENDING])
        rejected_leaves = len([l for l in leaves if l.status == LeaveStatus.REJECTED])
        
        return {
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "statistics": {
                "total_users": total_users,
                "total": total_leaves,
                "approved": approved_leaves,
                "pending": pending_leaves,
                "rejected": rejected_leaves
            },
            "leave_reports": report_data
        }
        
    except Exception as e:
        log_error(f"Get leaves report error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate leaves report"
        )

# Employee Management Endpoints for Admin (merged into User)
@router.post("/employees/{user_id}/details", response_model=UserResponse)
async def admin_create_employee_details(
    user_id: int,
    employee_data: EmployeeDetailsCreate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Initialize employee-related fields on the user (admin only)."""
    try:
        # Security: Validate user_id is positive integer
        if user_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID"
            )
        
        # Check if user exists and is active
        user_result = await db.execute(
            select(User).where(and_(User.id == user_id, User.is_active == True))
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active user not found"
            )
        
        # Security: Prevent admin from creating details for other admins
        if user.role == UserRole.ADMIN and user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot create employee details for other admin users"
            )
        
        # Validate manager_id if provided
        if employee_data.manager_id:
            manager_result = await db.execute(
                select(User).where(and_(User.id == employee_data.manager_id, User.is_active == True))
            )
            manager = manager_result.scalar_one_or_none()
            if not manager:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid manager ID"
                )
            # Prevent circular manager relationships
            if employee_data.manager_id == user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User cannot be their own manager"
                )
        # Apply fields onto User
        update_fields = employee_data.dict(exclude_unset=True)
        update_fields.pop('user_id', None)

        for field, value in update_fields.items():
            if hasattr(user, field):
                setattr(user, field, value)

        await db.commit()
        await db.refresh(user)
        log_info(f"Employee details initialized on user {user.email} by admin {current_user.email}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Admin create employee details error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create employee details"
        )

@router.put("/employees/{user_id}/details", response_model=UserResponse)
async def admin_update_employee_details(
    user_id: int,
    employee_data: EmployeeDetailsUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update employee-related fields on the user (admin only)."""
    try:
        # Security: Validate user_id is positive integer
        if user_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID"
            )
        
        # Load user
        result = await db.execute(select(User).where(User.id == user_id))
        user_obj = result.scalar_one_or_none()
        if not user_obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Security: Prevent admin from updating details for other admins
        if user_obj.role == UserRole.ADMIN and user_obj.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update employee details for other admin users"
            )
        
        # Validate manager_id if provided
        if employee_data.manager_id:
            manager_result = await db.execute(
                select(User).where(and_(User.id == employee_data.manager_id, User.is_active == True))
            )
            manager = manager_result.scalar_one_or_none()
            if not manager:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid manager ID"
                )
            # Prevent circular manager relationships
            if employee_data.manager_id == user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User cannot be their own manager"
                )
        
        # Update fields with validation on User
        update_data = employee_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(user_obj, field) and value is not None:
                setattr(user_obj, field, value)

        await db.commit()
        await db.refresh(user_obj)
        log_info(f"Employee details updated for user {user_id} by admin {current_user.email}")
        return user_obj
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Admin update employee details error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update employee details"
        )

@router.patch("/employees/{user_id}/details", response_model=UserResponse)
async def admin_patch_employee_details(
    user_id: int,
    employee_data: EmployeeDetailsUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Partially update employee-related fields on the user (admin only)."""
    try:
        # Security: Validate user_id is positive integer
        if user_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID"
            )
        
        # Load user
        result = await db.execute(select(User).where(User.id == user_id))
        user_obj = result.scalar_one_or_none()
        if not user_obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Security: Prevent admin from updating details for other admins
        if user_obj.role == UserRole.ADMIN and user_obj.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update employee details for other admin users"
            )
        
        # Validate manager_id if provided
        if employee_data.manager_id:
            manager_result = await db.execute(
                select(User).where(and_(User.id == employee_data.manager_id, User.is_active == True))
            )
            manager = manager_result.scalar_one_or_none()
            if not manager:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid manager ID"
                )
            # Prevent circular manager relationships
            if employee_data.manager_id == user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User cannot be their own manager"
                )
        
        # Update only provided fields (PATCH behavior)
        update_data = employee_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(user_obj, field) and value is not None:
                setattr(user_obj, field, value)

        await db.commit()
        await db.refresh(user_obj)
        log_info(f"Employee details patched for user {user_id} by admin {current_user.email}")
        return user_obj
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Admin patch employee details error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to patch employee details"
        )

@router.post("/employees/{user_id}/history", response_model=EmploymentHistoryResponse)
async def admin_create_employment_history(
    user_id: int,
    history_data: EmploymentHistoryCreate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create employment history for a user (admin only)."""
    try:
        # Security: Validate user_id is positive integer
        if user_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID"
            )
        
        # Check if user exists and is active
        user_result = await db.execute(
            select(User).where(and_(User.id == user_id, User.is_active == True))
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Active user not found"
            )
        
        # Security: Prevent admin from creating history for other admins
        if user.role == UserRole.ADMIN and user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot create employment history for other admin users"
            )
        
        # Validate manager_id if provided
        if history_data.manager_id:
            manager_result = await db.execute(
                select(User).where(and_(User.id == history_data.manager_id, User.is_active == True))
            )
            manager = manager_result.scalar_one_or_none()
            if not manager:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid manager ID"
                )
            # Prevent circular manager relationships
            if history_data.manager_id == user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User cannot be their own manager"
                )
        
        # Validate date logic
        if history_data.end_date and history_data.end_date < history_data.start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date cannot be before start date"
            )
        
        # If this is marked as current position, unmark all other current positions
        is_current = history_data.end_date is None
        if is_current:
            await db.execute(
                update(EmploymentHistory)
                .where(EmploymentHistory.user_id == user_id)
                .values(is_current=False)
            )
        
        # Create employment history with validated data
        history_dict = history_data.dict()
        history_dict['is_current'] = is_current
        employment_history = EmploymentHistory(user_id=user_id, **history_dict)
        db.add(employment_history)
        await db.commit()
        
        # Load with relationships to avoid async context issues
        result = await db.execute(
            select(EmploymentHistory)
            .options(
                selectinload(EmploymentHistory.user),
                selectinload(EmploymentHistory.manager)
            )
            .where(EmploymentHistory.id == employment_history.id)
        )
        employment_history = result.scalar_one_or_none()
        
        log_info(f"Employment history created for user {user.email} by admin {current_user.email}")
        return employment_history
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Admin create employment history error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create employment history"
        )

@router.get("/employees", response_model=List[EmployeeSummary])
async def admin_get_all_employees(
    offset: int = 0,
    limit: int = 10,
    department: str = None,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all employees with comprehensive details (admin only)."""
    try:
        # Get all users first
        result = await db.execute(
            select(User)
            .offset(offset)
            .limit(limit)
            .order_by(User.name)
        )
        users = result.scalars().all()
        
        employee_summaries = []
        for user in users:
            # With merged model, details are on the user
            employee_details = user

            # Skip by department if filtering
            if department and (not user.department or user.department != department):
                continue
            # Get current position
            current_position_result = await db.execute(
                select(EmploymentHistory)
                .where(
                    and_(
                        EmploymentHistory.user_id == user.id,
                        EmploymentHistory.is_current == True
                    )
                )
            )
            current_position = current_position_result.scalar_one_or_none()
            
            # Tracking disabled
            recent_tracking = []
            total_work_days = 0
            total_hours = 0
            average_hours_per_day = 0
            
            employee_summaries.append(EmployeeSummary(
                user=user,
                employee_details=user,
                current_position=current_position,
                recent_tracking=recent_tracking,
                total_work_days=total_work_days,
                average_hours_per_day=average_hours_per_day
            ))
        
        return employee_summaries
        
    except Exception as e:
        log_error(f"Admin get all employees error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch employees"
        )

@router.get("/employees/{user_id}/summary", response_model=EmployeeSummary)
async def admin_get_employee_summary(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive employee summary (admin only)."""
    try:
        # Get user
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # With merged model, details are the user object
        employee_details = user
        
        # Get current position
        current_position_result = await db.execute(
            select(EmploymentHistory)
            .options(
                selectinload(EmploymentHistory.user),
                selectinload(EmploymentHistory.manager)
            )
            .where(
                and_(
                    EmploymentHistory.user_id == user_id,
                    EmploymentHistory.is_current == True
                )
            )
        )
        current_position = current_position_result.scalar_one_or_none()
        
        # Tracking disabled
        recent_tracking = []
        total_work_days = 0
        total_hours = 0
        average_hours_per_day = 0
        
        return EmployeeSummary(
            user=user,
            employee_details=employee_details,
            current_position=current_position,
            recent_tracking=recent_tracking,
            total_work_days=total_work_days,
            average_hours_per_day=average_hours_per_day
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Admin get employee summary error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch employee summary"
        )

@router.get("/employees/departments")
async def admin_get_departments(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all departments with employee counts (admin only)."""
    try:
        result = await db.execute(
            select(User.department, func.count(User.id))
            .where(User.department.isnot(None))
            .group_by(User.department)
            .order_by(User.department)
        )
        departments = result.fetchall()
        
        return {
            "departments": [
                {"name": dept[0], "employee_count": dept[1]} 
                for dept in departments
            ]
        }
        
    except Exception as e:
        log_error(f"Admin get departments error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch departments"
        )


@router.get("/dashboard/enhanced")
async def get_enhanced_dashboard_stats(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get enhanced dashboard statistics with employee data (admin only)."""
    try:
        today = datetime.now().date()
        
        # Basic stats
        total_users = await db.execute(select(func.count(User.id)))
        total_users = total_users.scalar() or 0
        
        # Tracking disabled
        active_users_today = 0
        
        pending_leaves = await db.execute(
            select(func.count(Leave.id)).where(Leave.status == LeaveStatus.PENDING)
        )
        pending_leaves = pending_leaves.scalar() or 0
        
        # Employee-specific stats
        total_employees_with_details = await db.execute(select(func.count(User.id)))
        total_employees_with_details = total_employees_with_details.scalar() or 0
        
        # Department stats
        department_stats = await db.execute(
            select(User.department, func.count(User.id))
            .where(User.department.isnot(None))
            .group_by(User.department)
        )
        departments = department_stats.fetchall()
        
        # Recent activity (tracking disabled)
        recent_activity = []
        
        return {
            "basic_stats": {
                "total_users": total_users,
                "active_users_today": active_users_today,
                "pending_leaves": pending_leaves,
                "employees_with_details": total_employees_with_details
            },
            "departments": [
                {"name": dept[0], "count": dept[1]} 
                for dept in departments
            ],
            "recent_activity": recent_activity
        }
        
    except Exception as e:
        log_error(f"Enhanced dashboard stats error: {str(e)}")
        return {
            "basic_stats": {
                "total_users": 0,
                "active_users_today": 0,
                "pending_leaves": 0,
                "employees_with_details": 0
            },
            "departments": [],
            "recent_activity": []
        }
