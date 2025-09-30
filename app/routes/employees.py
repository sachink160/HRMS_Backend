from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func, desc, text
from sqlalchemy.orm import selectinload
from datetime import datetime, date, timedelta
from typing import List, Optional
from app.database import get_db
from app.models import User, EmployeeDetails, EmploymentHistory
from app.schema import (
    EmployeeDetailsCreate, EmployeeDetailsUpdate, EmployeeDetailsResponse,
    EmploymentHistoryCreate, EmploymentHistoryUpdate, EmploymentHistoryResponse,
    EmployeeSummary, EnhancedTrackerResponse, PaginationParams,
    ProbationReviewCreate, ProbationReviewUpdate, ProbationExtensionCreate,
    TerminationCreate, TerminationUpdate
)
from app.auth import get_current_user, get_current_admin_user
from app.logger import log_info, log_error
import json

router = APIRouter(prefix="/employees", tags=["employees"])

async def safe_get_employee_details(db: AsyncSession, user_id: int):
    """Safely get employee details, handling missing columns gracefully."""
    try:
        # Try to get employee details using ORM
        result = await db.execute(
            select(EmployeeDetails).where(EmployeeDetails.user_id == user_id)
        )
        return result.scalar_one_or_none()
    except Exception as e:
        log_error(f"Error fetching employee details for user {user_id}: {str(e)}")
        # If there's a schema mismatch, try to get basic info using raw SQL
        try:
            result = await db.execute(text("""
                SELECT id, user_id, employee_id, department, manager_id, 
                       employment_type, work_location, work_schedule, 
                       basic_salary, currency, is_active, created_at, updated_at
                FROM employee_details 
                WHERE user_id = :user_id
            """), {"user_id": user_id})
            row = result.fetchone()
            if row:
                # Create a minimal EmployeeDetails object with available fields
                from app.models import EmployeeDetails
                details = EmployeeDetails()
                details.id = row[0]
                details.user_id = row[1]
                details.employee_id = row[2]
                details.department = row[3]
                details.manager_id = row[4]
                details.employment_type = row[5]
                details.work_location = row[6]
                details.work_schedule = row[7]
                details.basic_salary = row[8]
                details.currency = row[9]
                details.is_active = row[10]
                details.created_at = row[11]
                details.updated_at = row[12]
                return details
        except Exception as e2:
            log_error(f"Error fetching employee details with raw SQL for user {user_id}: {str(e2)}")
        return None

# Employee Details Routes
@router.post("/details", response_model=EmployeeDetailsResponse)
async def create_employee_details(
    employee_data: EmployeeDetailsCreate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create employee details (admin only)."""
    try:
        # Check if user exists
        user_result = await db.execute(
            select(User).where(User.id == employee_data.user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if employee details already exist
        existing_details = await db.execute(
            select(EmployeeDetails).where(EmployeeDetails.user_id == employee_data.user_id)
        )
        if existing_details.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee details already exist for this user"
            )
        
        # Create employee details
        employee_details = EmployeeDetails(**employee_data.model_dump())
        db.add(employee_details)
        await db.commit()
        
        # Load with relationships to avoid async context issues
        result = await db.execute(
            select(EmployeeDetails)
            .options(
                selectinload(EmployeeDetails.user),
                selectinload(EmployeeDetails.manager)
            )
            .where(EmployeeDetails.user_id == employee_data.user_id)
        )
        employee_details = result.scalar_one_or_none()
        
        log_info(f"Employee details created for user {user.email}")
        return employee_details
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Create employee details error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create employee details"
        )

@router.get("/details/{user_id}", response_model=EmployeeDetailsResponse)
async def get_employee_details(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get employee details for a specific user."""
    try:
        # Check permissions - user can only view their own details unless admin
        if current_user.role.value not in ["admin", "super_admin"] and current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this employee's details"
            )
        
        result = await db.execute(
            select(EmployeeDetails)
            .options(
                selectinload(EmployeeDetails.user),
                selectinload(EmployeeDetails.manager)
            )
            .where(EmployeeDetails.user_id == user_id)
        )
        employee_details = result.scalar_one_or_none()
        
        if not employee_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee details not found"
            )
        
        return employee_details
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Get employee details error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch employee details"
        )

@router.put("/details/{user_id}", response_model=EmployeeDetailsResponse)
async def update_employee_details(
    user_id: int,
    employee_data: EmployeeDetailsUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update employee details (admin only)."""
    try:
        result = await db.execute(
            select(EmployeeDetails).where(EmployeeDetails.user_id == user_id)
        )
        employee_details = result.scalar_one_or_none()
        
        if not employee_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee details not found"
            )
        
        # Update fields
        update_data = employee_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(employee_details, field, value)
        
        await db.commit()
        
        # Refresh with relationships loaded
        await db.refresh(employee_details)
        
        # Load relationships explicitly to avoid async context issues
        result = await db.execute(
            select(EmployeeDetails)
            .options(
                selectinload(EmployeeDetails.user),
                selectinload(EmployeeDetails.manager)
            )
            .where(EmployeeDetails.user_id == user_id)
        )
        employee_details = result.scalar_one_or_none()
        
        log_info(f"Employee details updated for user {user_id}")
        return employee_details
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Update employee details error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update employee details"
        )

# Employment History Routes
@router.post("/history", response_model=EmploymentHistoryResponse)
async def create_employment_history(
    history_data: EmploymentHistoryCreate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create employment history record (admin only)."""
    try:
        # Check if user exists
        user_result = await db.execute(
            select(User).where(User.id == history_data.user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # If this is marked as current position, unmark all other current positions
        if history_data.end_date is None:  # Current position
            await db.execute(
                update(EmploymentHistory)
                .where(EmploymentHistory.user_id == history_data.user_id)
                .values(is_current=False)
            )
            history_data.is_current = True
        else:
            history_data.is_current = False
        
        # Create employment history
        employment_history = EmploymentHistory(**history_data.model_dump())
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
        
        log_info(f"Employment history created for user {user.email}")
        return employment_history
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Create employment history error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create employment history"
        )

@router.get("/history/{user_id}", response_model=List[EmploymentHistoryResponse])
async def get_employment_history(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get employment history for a specific user."""
    try:
        # Check permissions - user can only view their own history unless admin
        if current_user.role.value not in ["admin", "super_admin"] and current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this employee's history"
            )
        
        result = await db.execute(
            select(EmploymentHistory)
            .options(
                selectinload(EmploymentHistory.user),
                selectinload(EmploymentHistory.manager)
            )
            .where(EmploymentHistory.user_id == user_id)
            .order_by(desc(EmploymentHistory.start_date))
        )
        history = result.scalars().all()
        
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Get employment history error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch employment history"
        )

@router.put("/history/{history_id}", response_model=EmploymentHistoryResponse)
async def update_employment_history(
    history_id: int,
    history_data: EmploymentHistoryUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update employment history record (admin only)."""
    try:
        result = await db.execute(
            select(EmploymentHistory).where(EmploymentHistory.id == history_id)
        )
        employment_history = result.scalar_one_or_none()
        
        if not employment_history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employment history record not found"
            )
        
        # Update fields
        update_data = history_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(employment_history, field, value)
        
        # If marking as current, unmark all other current positions
        if employment_history.is_current:
            await db.execute(
                update(EmploymentHistory)
                .where(
                    and_(
                        EmploymentHistory.user_id == employment_history.user_id,
                        EmploymentHistory.id != history_id
                    )
                )
                .values(is_current=False)
            )
        
        await db.commit()
        
        # Load with relationships to avoid async context issues
        result = await db.execute(
            select(EmploymentHistory)
            .options(
                selectinload(EmploymentHistory.user),
                selectinload(EmploymentHistory.manager)
            )
            .where(EmploymentHistory.id == history_id)
        )
        employment_history = result.scalar_one_or_none()
        
        log_info(f"Employment history updated for record {history_id}")
        return employment_history
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Update employment history error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update employment history"
        )

# Employee Summary Routes
@router.get("/summary/{user_id}", response_model=EmployeeSummary)
async def get_employee_summary(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive employee summary including details, history, and tracking."""
    try:
        # Check permissions - user can only view their own summary unless admin
        if current_user.role.value not in ["admin", "super_admin"] and current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this employee's summary"
            )
        
        # Get user
        user_result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get employee details
        details_result = await db.execute(
            select(EmployeeDetails)
            .options(
                selectinload(EmployeeDetails.user),
                selectinload(EmployeeDetails.manager)
            )
            .where(EmployeeDetails.user_id == user_id)
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
                    EmploymentHistory.user_id == user_id,
                    EmploymentHistory.is_current == True
                )
            )
        )
        current_position = current_position_result.scalar_one_or_none()
        
        # Skip tracking logic for now - not needed for basic employee summary
        recent_tracking = []
        total_work_days = 0
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
        log_error(f"Get employee summary error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch employee summary"
        )

@router.get("/list", response_model=List[EmployeeSummary])
async def get_all_employees_summary(
    offset: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get summary of all employees (admin only)."""
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
            # Get employee details for this user safely
            employee_details = await safe_get_employee_details(db, user.id)
            
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
                
            # Skip tracking logic for now - not needed for basic employee summary
            recent_tracking = []
            total_work_days = 0
            average_hours_per_day = 0
            
            employee_summaries.append(EmployeeSummary(
                user=user,
                employee_details=employee_details,
                current_position=current_position,
                recent_tracking=recent_tracking,
                total_work_days=total_work_days,
                average_hours_per_day=average_hours_per_day
            ))
        
        return employee_summaries
        
    except Exception as e:
        log_error(f"Get all employees summary error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch employees summary"
        )

# Department-wise employee listing
@router.get("/department/{department}", response_model=List[EmployeeSummary])
async def get_employees_by_department(
    department: str,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get employees by department (admin only)."""
    try:
        # Get users with employee details in specific department
        result = await db.execute(
            select(User)
            .join(EmployeeDetails)
            .where(EmployeeDetails.department == department)
            .order_by(User.name)
        )
        users = result.scalars().all()
        
        employee_summaries = []
        for user in users:
            # Get employee details for this user safely
            employee_details = await safe_get_employee_details(db, user.id)
            
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
            
            employee_summaries.append(EmployeeSummary(
                user=user,
                employee_details=employee_details,
                current_position=current_position,
                recent_tracking=[],
                total_work_days=0,
                average_hours_per_day=0
            ))
        
        return employee_summaries
        
    except Exception as e:
        log_error(f"Get employees by department error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch employees by department"
        )

# Probation Management Routes
@router.post("/{user_id}/probation/review", response_model=EmployeeDetailsResponse)
async def review_probation(
    user_id: int,
    review_data: ProbationReviewCreate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Review employee probation (admin only)."""
    try:
        # Get employee details
        result = await db.execute(
            select(EmployeeDetails).where(EmployeeDetails.user_id == user_id)
        )
        employee_details = result.scalar_one_or_none()
        
        if not employee_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee details not found"
            )
        
        # Update probation review data
        employee_details.probation_status = review_data.probation_status
        employee_details.probation_review_date = review_data.probation_review_date
        employee_details.probation_review_notes = review_data.probation_review_notes
        employee_details.probation_reviewer_id = review_data.probation_reviewer_id
        
        # If probation is passed, set end date
        if review_data.probation_status == "passed":
            employee_details.probation_end_date = review_data.probation_review_date
        
        await db.commit()
        
        # Load with relationships
        result = await db.execute(
            select(EmployeeDetails)
            .options(
                selectinload(EmployeeDetails.user),
                selectinload(EmployeeDetails.manager),
                selectinload(EmployeeDetails.probation_reviewer)
            )
            .where(EmployeeDetails.user_id == user_id)
        )
        employee_details = result.scalar_one_or_none()
        
        log_info(f"Probation reviewed for user {user_id} by admin {current_user.email}")
        return employee_details
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Review probation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to review probation"
        )

@router.post("/{user_id}/probation/extend", response_model=EmployeeDetailsResponse)
async def extend_probation(
    user_id: int,
    extension_data: ProbationExtensionCreate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Extend employee probation period (admin only)."""
    try:
        # Get employee details
        result = await db.execute(
            select(EmployeeDetails).where(EmployeeDetails.user_id == user_id)
        )
        employee_details = result.scalar_one_or_none()
        
        if not employee_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee details not found"
            )
        
        # Calculate new probation end date
        if employee_details.probation_end_date:
            from datetime import timedelta
            new_end_date = employee_details.probation_end_date + timedelta(days=extension_data.extension_months * 30)
        else:
            new_end_date = date.today() + timedelta(days=extension_data.extension_months * 30)
        
        # Update probation data
        employee_details.probation_status = "extended"
        employee_details.probation_end_date = new_end_date
        employee_details.probation_period_months += extension_data.extension_months
        employee_details.probation_review_notes = f"Extended by {extension_data.extension_months} months. Reason: {extension_data.extension_reason}"
        employee_details.probation_reviewer_id = extension_data.probation_reviewer_id
        employee_details.probation_review_date = date.today()
        
        await db.commit()
        
        # Load with relationships
        result = await db.execute(
            select(EmployeeDetails)
            .options(
                selectinload(EmployeeDetails.user),
                selectinload(EmployeeDetails.manager),
                selectinload(EmployeeDetails.probation_reviewer)
            )
            .where(EmployeeDetails.user_id == user_id)
        )
        employee_details = result.scalar_one_or_none()
        
        log_info(f"Probation extended for user {user_id} by admin {current_user.email}")
        return employee_details
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Extend probation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extend probation"
        )

@router.get("/probation/pending", response_model=List[EmployeeDetailsResponse])
async def get_pending_probation_reviews(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get employees with pending probation reviews (admin only)."""
    try:
        result = await db.execute(
            select(EmployeeDetails)
            .options(
                selectinload(EmployeeDetails.user),
                selectinload(EmployeeDetails.manager)
            )
            .where(
                and_(
                    EmployeeDetails.probation_status == "pending",
                    EmployeeDetails.probation_end_date <= date.today()
                )
            )
        )
        pending_reviews = result.scalars().all()
        
        return pending_reviews
        
    except Exception as e:
        log_error(f"Get pending probation reviews error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch pending probation reviews"
        )

# Termination Management Routes
@router.post("/{user_id}/terminate", response_model=EmployeeDetailsResponse)
async def terminate_employee(
    user_id: int,
    termination_data: TerminationCreate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Terminate employee (admin only)."""
    try:
        # Get employee details
        result = await db.execute(
            select(EmployeeDetails).where(EmployeeDetails.user_id == user_id)
        )
        employee_details = result.scalar_one_or_none()
        
        if not employee_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee details not found"
            )
        
        # Update termination data
        employee_details.termination_date = termination_data.termination_date
        employee_details.termination_reason = termination_data.termination_reason
        employee_details.termination_type = termination_data.termination_type
        employee_details.termination_notice_period_days = termination_data.termination_notice_period_days
        employee_details.last_working_date = termination_data.last_working_date
        employee_details.termination_notes = termination_data.termination_notes
        employee_details.termination_initiated_by = termination_data.termination_initiated_by
        employee_details.is_active = False
        
        # Deactivate user account
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if user:
            user.is_active = False
        
        await db.commit()
        
        # Load with relationships
        result = await db.execute(
            select(EmployeeDetails)
            .options(
                selectinload(EmployeeDetails.user),
                selectinload(EmployeeDetails.manager),
                selectinload(EmployeeDetails.termination_initiator)
            )
            .where(EmployeeDetails.user_id == user_id)
        )
        employee_details = result.scalar_one_or_none()
        
        log_info(f"Employee {user_id} terminated by admin {current_user.email}")
        return employee_details
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Terminate employee error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to terminate employee"
        )

@router.put("/{user_id}/termination", response_model=EmployeeDetailsResponse)
async def update_termination_details(
    user_id: int,
    termination_data: TerminationUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update termination details (admin only)."""
    try:
        # Get employee details
        result = await db.execute(
            select(EmployeeDetails).where(EmployeeDetails.user_id == user_id)
        )
        employee_details = result.scalar_one_or_none()
        
        if not employee_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee details not found"
            )
        
        # Update termination data
        update_data = termination_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(employee_details, field, value)
        
        await db.commit()
        
        # Load with relationships
        result = await db.execute(
            select(EmployeeDetails)
            .options(
                selectinload(EmployeeDetails.user),
                selectinload(EmployeeDetails.manager),
                selectinload(EmployeeDetails.termination_initiator)
            )
            .where(EmployeeDetails.user_id == user_id)
        )
        employee_details = result.scalar_one_or_none()
        
        log_info(f"Termination details updated for user {user_id} by admin {current_user.email}")
        return employee_details
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Update termination details error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update termination details"
        )

@router.get("/terminated", response_model=List[EmployeeDetailsResponse])
async def get_terminated_employees(
    offset: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get terminated employees (admin only)."""
    try:
        result = await db.execute(
            select(EmployeeDetails)
            .options(
                selectinload(EmployeeDetails.user),
                selectinload(EmployeeDetails.manager),
                selectinload(EmployeeDetails.termination_initiator)
            )
            .where(EmployeeDetails.termination_date.isnot(None))
            .offset(offset)
            .limit(limit)
            .order_by(EmployeeDetails.termination_date.desc())
        )
        terminated_employees = result.scalars().all()
        
        return terminated_employees
        
    except Exception as e:
        log_error(f"Get terminated employees error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch terminated employees"
        )
