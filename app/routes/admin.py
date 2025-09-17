from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from fastapi import UploadFile, File
from pathlib import Path
import uuid
from sqlalchemy.orm import selectinload
from datetime import datetime, date
from typing import List, Dict, Any
from app.database import get_db
from app.models import User, Leave, Holiday, UserTracker, LeaveStatus, UserRole, DocumentStatus
from app.schema import UserResponse, LeaveResponse, HolidayResponse, TrackerResponse, UserCreate
from app.auth import get_current_admin_user, get_password_hash, get_current_super_admin_user
from app.logger import log_info, log_error

router = APIRouter(prefix="/admin", tags=["admin"])
# Helpers for file upload (duplicate of users router helpers)
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024

def _validate_file(file: UploadFile) -> bool:
    if not file.filename:
        return False
    ext = Path(file.filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS

async def _save_uploaded_file(file: UploadFile, user_id: int, document_type: str) -> str:
    if not _validate_file(file):
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPG, PNG, and PDF files are allowed.")
    ext = Path(file.filename).suffix.lower()
    unique_filename = f"{user_id}_{document_type}_{uuid.uuid4()}{ext}"
    file_path = UPLOAD_DIR / unique_filename
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size too large. Maximum size is 10MB.")
    with open(file_path, "wb") as f:
        f.write(content)
    return str(file_path)

# Super admin can upload documents for any user
@router.post("/users/{user_id}/upload-profile-image")
async def admin_upload_profile_image(
    user_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_super_admin_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        target_user = result.scalar_one_or_none()
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        file_path = await _save_uploaded_file(file, user_id, "profile")
        target_user.profile_image = file_path
        target_user.profile_image_status = DocumentStatus.APPROVED
        await db.commit()
        return {"file_path": file_path}
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Admin upload profile image error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload profile image")

@router.post("/users/{user_id}/upload-aadhaar-front")
async def admin_upload_aadhaar_front(
    user_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_super_admin_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        target_user = result.scalar_one_or_none()
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        file_path = await _save_uploaded_file(file, user_id, "aadhaar_front")
        target_user.aadhaar_front = file_path
        target_user.aadhaar_front_status = DocumentStatus.APPROVED
        await db.commit()
        return {"file_path": file_path}
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Admin upload aadhaar front error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload Aadhaar front")

@router.post("/users/{user_id}/upload-aadhaar-back")
async def admin_upload_aadhaar_back(
    user_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_super_admin_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        target_user = result.scalar_one_or_none()
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        file_path = await _save_uploaded_file(file, user_id, "aadhaar_back")
        target_user.aadhaar_back = file_path
        target_user.aadhaar_back_status = DocumentStatus.APPROVED
        await db.commit()
        return {"file_path": file_path}
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Admin upload aadhaar back error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload Aadhaar back")

@router.post("/users/{user_id}/upload-pan")
async def admin_upload_pan(
    user_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_super_admin_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        target_user = result.scalar_one_or_none()
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        file_path = await _save_uploaded_file(file, user_id, "pan")
        target_user.pan_image = file_path
        target_user.pan_image_status = DocumentStatus.APPROVED
        await db.commit()
        return {"file_path": file_path}
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
            
            # Get active users today (safe)
            try:
                active_users_result = await db.execute(
                    select(func.count(UserTracker.user_id.distinct())).where(
                        and_(
                            func.date(UserTracker.date) == today,
                            UserTracker.check_in.isnot(None)
                        )
                    )
                )
                active_users = active_users_result.scalar() or 0
            except Exception as e:
                log_error(f"Error getting active users: {str(e)}")
                # If UserTracker table doesn't exist, return 0
            
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
    user_data: dict,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user information (admin only)."""
    try:
        # Get user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if trying to update super admin
        if user.role == UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update super admin user"
            )
        
        # Validate role if provided
        if 'role' in user_data:
            if user_data['role'] not in [UserRole.USER, UserRole.ADMIN]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid role. Must be 'user' or 'admin'"
                )
        
        # Check email uniqueness if email is being updated
        if 'email' in user_data and user_data['email'] != user.email:
            existing_user = await db.execute(select(User).where(User.email == user_data['email']))
            if existing_user.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        
        # Update user fields
        if 'name' in user_data:
            user.name = user_data['name']
        if 'email' in user_data:
            user.email = user_data['email']
        if 'phone' in user_data:
            user.phone = user_data['phone']
        if 'designation' in user_data:
            user.designation = user_data['designation']
        if 'joining_date' in user_data:
            jd = user_data['joining_date']
            try:
                if isinstance(jd, str) and jd:
                    # Accept formats like 'YYYY-MM-DD' or ISO datetime
                    try:
                        parsed = datetime.strptime(jd, "%Y-%m-%d").date()
                    except ValueError:
                        parsed = datetime.fromisoformat(jd).date()
                    user.joining_date = parsed
                elif isinstance(jd, date):
                    user.joining_date = jd
                elif jd in (None, ""):
                    user.joining_date = None
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid joining_date format. Expected YYYY-MM-DD"
                )
        if 'role' in user_data:
            user.role = user_data['role']

        # Final safeguard: ensure joining_date is a date object before committing
        try:
            if isinstance(user.joining_date, str):
                try:
                    user.joining_date = datetime.strptime(user.joining_date, "%Y-%m-%d").date()
                except ValueError:
                    user.joining_date = datetime.fromisoformat(user.joining_date).date()
        except Exception:
            pass

        await db.commit()
        await db.refresh(user)
        
        log_info(f"User {user_id} updated by admin {current_user.email}")
        return user
        
    except Exception as e:
        log_error(f"Update user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
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
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all leave applications with optional status filter (admin only)."""
    try:
        query = select(Leave).options(selectinload(Leave.user))
        
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

@router.get("/tracking", response_model=List[TrackerResponse])
async def get_all_tracking(
    offset: int = 0,
    limit: int = 10,
    date_filter: str = None,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all tracking records with optional date filter (admin only)."""
    try:
        query = select(UserTracker).options(selectinload(UserTracker.user))
        
        if date_filter:
            filter_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
            query = query.where(UserTracker.date == filter_date)
        
        result = await db.execute(
            query
            .offset(offset)
            .limit(limit)
            .order_by(UserTracker.date.desc())
        )
        trackers = result.scalars().all()
        return trackers
        
    except Exception as e:
        log_error(f"Get all tracking error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch tracking records"
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
        
        # Get user's recent tracking
        tracking_result = await db.execute(
            select(UserTracker)
            .where(UserTracker.user_id == user_id)
            .order_by(UserTracker.date.desc())
            .limit(30)
        )
        tracking = tracking_result.scalars().all()
        
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
        result = await db.execute(select(Leave).where(Leave.id == leave_id))
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
        result = await db.execute(select(Leave).where(Leave.id == leave_id))
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
            # Check if holiday already exists
            existing_holiday = await db.execute(
                select(Holiday).where(Holiday.date == holiday_data["date"])
            )
            if existing_holiday.scalar_one_or_none():
                continue  # Skip if already exists
            
            # Create holiday
            db_holiday = Holiday(
                date=holiday_data["date"],
                title=holiday_data["title"],
                description=holiday_data.get("description")
            )
            db.add(db_holiday)
            created_holidays.append(db_holiday)
        
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

@router.get("/reports/attendance")
async def get_attendance_report(
    start_date: str = None,
    end_date: str = None,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get attendance report for date range (admin only)."""
    try:
        query = select(UserTracker).options(selectinload(UserTracker.user))
        
        if start_date and end_date:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
            query = query.where(
                and_(
                    UserTracker.date >= start,
                    UserTracker.date <= end
                )
            )
        
        result = await db.execute(query.order_by(UserTracker.date.desc()))
        trackers = result.scalars().all()
        
        # Group by user
        user_attendance = {}
        for tracker in trackers:
            user_id = tracker.user_id
            if user_id not in user_attendance:
                user_attendance[user_id] = {
                    "user": tracker.user,
                    "records": []
                }
            user_attendance[user_id]["records"].append(tracker)
        
        return {
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "attendance": list(user_attendance.values())
        }
        
    except Exception as e:
        log_error(f"Get attendance report error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate attendance report"
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
        
        user.is_active = not user.is_active
        await db.commit()
        await db.refresh(user)
        
        status_text = "activated" if user.is_active else "deactivated"
        log_info(f"User {user_id} {status_text} by admin {current_user.email}")
        return {"message": f"User {status_text} successfully", "user": user}
        
    except Exception as e:
        log_error(f"Toggle user status error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle user status"
        )

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
        
        # Check if trying to delete super admin
        if user.role == UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete super admin user"
            )
        
        # Check if trying to delete own account
        if user.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        # Delete related records first
        # Delete user trackers
        from app.models import UserTracker
        trackers_result = await db.execute(
            select(UserTracker).where(UserTracker.user_id == user_id)
        )
        trackers = trackers_result.scalars().all()
        for tracker in trackers:
            await db.delete(tracker)
        
        # Delete user leaves
        from app.models import Leave
        leaves_result = await db.execute(
            select(Leave).where(Leave.user_id == user_id)
        )
        leaves = leaves_result.scalars().all()
        for leave in leaves:
            await db.delete(leave)
        
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
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive leaves report (admin only)."""
    try:
        query = select(Leave).options(selectinload(Leave.user))
        
        if start_date and end_date:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
            query = query.where(
                and_(
                    Leave.start_date >= start,
                    Leave.end_date <= end
                )
            )
        
        if status_filter:
            query = query.where(Leave.status == status_filter)
        
        result = await db.execute(query.order_by(Leave.created_at.desc()))
        leaves = result.scalars().all()
        
        # Calculate statistics
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
                "total": total_leaves,
                "approved": approved_leaves,
                "pending": pending_leaves,
                "rejected": rejected_leaves
            },
            "leaves": leaves
        }
        
    except Exception as e:
        log_error(f"Get leaves report error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate leaves report"
        )
