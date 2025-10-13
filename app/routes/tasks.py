from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timezone

from app.database import get_db
from app.auth import get_current_user
from app.models import User, Task, TaskStatus, UserRole
from app.schema import (
    TaskCreate, TaskUpdate, TaskResponse, TaskSummary, 
    PaginationParams, PaginatedResponse
)
from app.logger import log_info, log_error

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("/", response_model=TaskResponse)
async def create_task(
    task: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new task for the current user."""
    try:
        # Create new task
        db_task = Task(
            user_id=current_user.id,
            name=task.name,
            description=task.description,
            due_date=task.due_date,
            priority=task.priority,
            category=task.category,
            status=TaskStatus.PENDING
        )
        
        db.add(db_task)
        await db.commit()
        await db.refresh(db_task)
        
        # Load user relationship for response
        await db.refresh(db_task, ['user'])
        
        log_info(f"Task created successfully for user {current_user.email}: {task.name}")
        return db_task
        
    except Exception as e:
        await db.rollback()
        log_error(f"Error creating task: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create task")

@router.get("/my-tasks", response_model=List[TaskResponse])
async def get_my_tasks(
    status: Optional[TaskStatus] = Query(None, description="Filter by task status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    category: Optional[str] = Query(None, description="Filter by category"),
    overdue_only: bool = Query(False, description="Show only overdue tasks"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all tasks for the current user."""
    try:
        query = select(Task).where(
            and_(
                Task.user_id == current_user.id,
                Task.is_active == True
            )
        ).options(selectinload(Task.user))
        
        # Apply filters
        if status:
            query = query.where(Task.status == status)
        
        if priority:
            query = query.where(Task.priority == priority)
        
        if category:
            query = query.where(Task.category == category)
        
        if overdue_only:
            query = query.where(
                and_(
                    Task.due_date < datetime.now(timezone.utc),
                    Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
                )
            )
        
        query = query.order_by(Task.created_at.desc())
        
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        log_info(f"Retrieved {len(tasks)} tasks for user {current_user.email}")
        return tasks
        
    except Exception as e:
        log_error(f"Error retrieving user tasks: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve tasks")

@router.get("/my-tasks/summary", response_model=TaskSummary)
async def get_my_task_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get task summary for the current user."""
    try:
        # Get task counts by status
        total_query = select(func.count(Task.id)).where(
            and_(
                Task.user_id == current_user.id,
                Task.is_active == True
            )
        )
        
        pending_query = select(func.count(Task.id)).where(
            and_(
                Task.user_id == current_user.id,
                Task.is_active == True,
                Task.status == TaskStatus.PENDING
            )
        )
        
        in_progress_query = select(func.count(Task.id)).where(
            and_(
                Task.user_id == current_user.id,
                Task.is_active == True,
                Task.status == TaskStatus.IN_PROGRESS
            )
        )
        
        completed_query = select(func.count(Task.id)).where(
            and_(
                Task.user_id == current_user.id,
                Task.is_active == True,
                Task.status == TaskStatus.COMPLETED
            )
        )
        
        cancelled_query = select(func.count(Task.id)).where(
            and_(
                Task.user_id == current_user.id,
                Task.is_active == True,
                Task.status == TaskStatus.CANCELLED
            )
        )
        
        overdue_query = select(func.count(Task.id)).where(
            and_(
                Task.user_id == current_user.id,
                Task.is_active == True,
                Task.due_date < datetime.now(timezone.utc),
                Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
            )
        )
        
        # Execute all queries
        total_result = await db.execute(total_query)
        pending_result = await db.execute(pending_query)
        in_progress_result = await db.execute(in_progress_query)
        completed_result = await db.execute(completed_query)
        cancelled_result = await db.execute(cancelled_query)
        overdue_result = await db.execute(overdue_query)
        
        summary = TaskSummary(
            total_tasks=total_result.scalar() or 0,
            pending_tasks=pending_result.scalar() or 0,
            in_progress_tasks=in_progress_result.scalar() or 0,
            completed_tasks=completed_result.scalar() or 0,
            cancelled_tasks=cancelled_result.scalar() or 0,
            overdue_tasks=overdue_result.scalar() or 0
        )
        
        log_info(f"Task summary retrieved for user {current_user.email}")
        return summary
        
    except Exception as e:
        log_error(f"Error retrieving task summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve task summary")

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific task by ID."""
    try:
        query = select(Task).where(
            and_(
                Task.id == task_id,
                Task.user_id == current_user.id,
                Task.is_active == True
            )
        ).options(selectinload(Task.user))
        
        result = await db.execute(query)
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        log_info(f"Task {task_id} retrieved for user {current_user.email}")
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Error retrieving task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve task")

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a specific task."""
    try:
        query = select(Task).where(
            and_(
                Task.id == task_id,
                Task.user_id == current_user.id,
                Task.is_active == True
            )
        )
        
        result = await db.execute(query)
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Update task fields
        update_data = task_update.model_dump(exclude_unset=True)
        
        # Handle status change to completed
        if 'status' in update_data and update_data['status'] == TaskStatus.COMPLETED:
            update_data['completed_at'] = datetime.now(timezone.utc)
        
        for field, value in update_data.items():
            setattr(task, field, value)
        
        await db.commit()
        await db.refresh(task, ['user'])
        
        log_info(f"Task {task_id} updated for user {current_user.email}")
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        log_error(f"Error updating task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update task")

@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a specific task (soft delete)."""
    try:
        query = select(Task).where(
            and_(
                Task.id == task_id,
                Task.user_id == current_user.id,
                Task.is_active == True
            )
        )
        
        result = await db.execute(query)
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Soft delete
        task.is_active = False
        await db.commit()
        
        log_info(f"Task {task_id} deleted for user {current_user.email}")
        return {"message": "Task deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        log_error(f"Error deleting task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete task")

# Admin/Super Admin Routes
@router.get("/admin/all-tasks", response_model=PaginatedResponse)
async def get_all_tasks_admin(
    status: Optional[TaskStatus] = Query(None, description="Filter by task status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    category: Optional[str] = Query(None, description="Filter by category"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    overdue_only: bool = Query(False, description="Show only overdue tasks"),
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all tasks across all users (Admin/Super Admin only)."""
    try:
        # Check if user is admin or super admin
        if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            raise HTTPException(status_code=403, detail="Access denied. Admin privileges required.")
        
        # Build query
        query = select(Task).where(Task.is_active == True).options(selectinload(Task.user))
        
        # Apply filters
        if status:
            query = query.where(Task.status == status)
        
        if priority:
            query = query.where(Task.priority == priority)
        
        if category:
            query = query.where(Task.category == category)
        
        if user_id:
            query = query.where(Task.user_id == user_id)
        
        if overdue_only:
            query = query.where(
                and_(
                    Task.due_date < datetime.now(timezone.utc),
                    Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
                )
            )
        
        # Get total count
        count_query = select(func.count(Task.id)).where(Task.is_active == True)
        if status:
            count_query = count_query.where(Task.status == status)
        if priority:
            count_query = count_query.where(Task.priority == priority)
        if category:
            count_query = count_query.where(Task.category == category)
        if user_id:
            count_query = count_query.where(Task.user_id == user_id)
        if overdue_only:
            count_query = count_query.where(
                and_(
                    Task.due_date < datetime.now(timezone.utc),
                    Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
                )
            )
        
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Get paginated results
        query = query.order_by(Task.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        # Convert to dict for response
        task_dicts = []
        for task in tasks:
            task_dict = {
                "id": task.id,
                "name": task.name,
                "description": task.description,
                "status": task.status,
                "priority": task.priority,
                "category": task.category,
                "due_date": task.due_date,
                "completed_at": task.completed_at,
                "created_at": task.created_at,
                "updated_at": task.updated_at,
                "user": {
                    "id": task.user.id,
                    "name": task.user.name,
                    "email": task.user.email,
                    "designation": task.user.designation
                } if task.user else None
            }
            task_dicts.append(task_dict)
        
        log_info(f"Admin {current_user.email} retrieved {len(tasks)} tasks")
        return PaginatedResponse(
            items=task_dicts,
            total=total,
            offset=offset,
            limit=limit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Error retrieving all tasks for admin: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve tasks")

@router.get("/admin/summary", response_model=TaskSummary)
async def get_admin_task_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get task summary across all users (Admin/Super Admin only)."""
    try:
        # Check if user is admin or super admin
        if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            raise HTTPException(status_code=403, detail="Access denied. Admin privileges required.")
        
        # Get task counts by status
        total_query = select(func.count(Task.id)).where(Task.is_active == True)
        pending_query = select(func.count(Task.id)).where(
            and_(Task.is_active == True, Task.status == TaskStatus.PENDING)
        )
        in_progress_query = select(func.count(Task.id)).where(
            and_(Task.is_active == True, Task.status == TaskStatus.IN_PROGRESS)
        )
        completed_query = select(func.count(Task.id)).where(
            and_(Task.is_active == True, Task.status == TaskStatus.COMPLETED)
        )
        cancelled_query = select(func.count(Task.id)).where(
            and_(Task.is_active == True, Task.status == TaskStatus.CANCELLED)
        )
        overdue_query = select(func.count(Task.id)).where(
            and_(
                Task.is_active == True,
                Task.due_date < datetime.now(timezone.utc),
                Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
            )
        )
        
        # Execute all queries
        total_result = await db.execute(total_query)
        pending_result = await db.execute(pending_query)
        in_progress_result = await db.execute(in_progress_query)
        completed_result = await db.execute(completed_query)
        cancelled_result = await db.execute(cancelled_query)
        overdue_result = await db.execute(overdue_query)
        
        summary = TaskSummary(
            total_tasks=total_result.scalar() or 0,
            pending_tasks=pending_result.scalar() or 0,
            in_progress_tasks=in_progress_result.scalar() or 0,
            completed_tasks=completed_result.scalar() or 0,
            cancelled_tasks=cancelled_result.scalar() or 0,
            overdue_tasks=overdue_result.scalar() or 0
        )
        
        log_info(f"Admin task summary retrieved for user {current_user.email}")
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Error retrieving admin task summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve task summary")
