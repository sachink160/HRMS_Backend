from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from datetime import datetime, date
from typing import List, Dict, Any
from app.database import get_db
from app.models import User, Leave, Holiday, UserTracker, LeaveStatus, UserRole
from app.schema import UserResponse, LeaveResponse, HolidayResponse, TrackerResponse
from app.auth import get_current_admin_user
from app.logger import log_info, log_error

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/dashboard")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard statistics (admin only)."""
    try:
        # Total users
        total_users_result = await db.execute(select(func.count(User.id)))
        total_users = total_users_result.scalar()
        
        # Active users (checked in today)
        today = datetime.now().date()
        active_users_result = await db.execute(
            select(func.count(UserTracker.user_id.distinct())).where(
                and_(
                    UserTracker.date == today,
                    UserTracker.check_in.isnot(None)
                )
            )
        )
        active_users = active_users_result.scalar()
        
        # Pending leaves
        pending_leaves_result = await db.execute(
            select(func.count(Leave.id)).where(Leave.status == LeaveStatus.PENDING)
        )
        pending_leaves = pending_leaves_result.scalar()
        
        # Upcoming holidays
        upcoming_holidays_result = await db.execute(
            select(func.count(Holiday.id)).where(Holiday.date >= today)
        )
        upcoming_holidays = upcoming_holidays_result.scalar()
        
        return {
            "total_users": total_users,
            "active_users_today": active_users,
            "pending_leaves": pending_leaves,
            "upcoming_holidays": upcoming_holidays
        }
        
    except Exception as e:
        log_error(f"Dashboard stats error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch dashboard statistics"
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
