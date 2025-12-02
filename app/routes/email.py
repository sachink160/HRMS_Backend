from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models import User, EmailSettings, EmailTemplate, EmailLog
from app.schema import (
    EmailSettingsCreate, EmailSettingsUpdate, EmailSettingsResponse,
    EmailTemplateCreate, EmailTemplateUpdate, EmailTemplateResponse,
    EmailSendRequest, EmailBulkSendRequest, EmailLogResponse,
    PaginationParams, PaginatedResponse
)
from app.auth import get_current_admin_user
from app.fastapi_email_service import fastapi_email_service
from app.logger import log_info, log_error

router = APIRouter(prefix="/email", tags=["email-management"])

# Email Settings Routes
@router.get("/settings", response_model=EmailSettingsResponse)
async def get_email_settings(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current email settings."""
    try:
        result = await db.execute(
            select(EmailSettings).where(EmailSettings.is_active == True)
        )
        settings = result.scalar_one_or_none()
        
        if not settings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No email settings configured"
            )
        
        return settings
    except HTTPException:
        # Re-raise HTTPException as-is (for 404, etc.)
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        log_error(f"Failed to get email settings: {str(e)}\n{error_trace}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve email settings: {str(e)}"
        )

@router.post("/settings", response_model=EmailSettingsResponse)
async def create_email_settings(
    settings_data: EmailSettingsCreate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new email settings."""
    try:
        # Deactivate existing settings
        await db.execute(
            select(EmailSettings).where(EmailSettings.is_active == True)
        )
        existing_settings = await db.execute(
            select(EmailSettings).where(EmailSettings.is_active == True)
        )
        if existing_settings.scalar_one_or_none():
            await db.execute(
                EmailSettings.__table__.update().where(
                    EmailSettings.is_active == True
                ).values(is_active=False)
            )
        
        # Create new settings
        new_settings = EmailSettings(**settings_data.dict())
        db.add(new_settings)
        await db.commit()
        await db.refresh(new_settings)
        
        # Reload email service settings
        await fastapi_email_service.load_settings(db)
        
        log_info(f"Email settings created by {current_user.email}")
        return new_settings
    except Exception as e:
        log_error(f"Failed to create email settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create email settings"
        )

@router.put("/settings/{settings_id}", response_model=EmailSettingsResponse)
async def update_email_settings(
    settings_id: int,
    settings_data: EmailSettingsUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update email settings."""
    try:
        result = await db.execute(
            select(EmailSettings).where(EmailSettings.id == settings_id)
        )
        settings = result.scalar_one_or_none()
        
        if not settings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email settings not found"
            )
        
        # Update fields
        update_data = settings_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(settings, field, value)
        
        await db.commit()
        await db.refresh(settings)
        
        # Reload email service settings
        await fastapi_email_service.load_settings(db)
        
        log_info(f"Email settings updated by {current_user.email}")
        return settings
    except Exception as e:
        log_error(f"Failed to update email settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update email settings"
        )

@router.post("/settings/test-connection")
async def test_email_connection(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Test email connection with current settings."""
    try:
        await fastapi_email_service.load_settings(db)
        success = await fastapi_email_service.test_connection()
        
        return {
            "success": success,
            "message": "Connection test successful" if success else "Connection test failed"
        }
    except Exception as e:
        log_error(f"Email connection test failed: {str(e)}")
        return {
            "success": False,
            "message": f"Connection test failed: {str(e)}"
        }

# Email Templates Routes
@router.get("/templates", response_model=List[EmailTemplateResponse])
async def get_email_templates(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all email templates."""
    try:
        result = await db.execute(select(EmailTemplate))
        templates = result.scalars().all()
        return templates
    except Exception as e:
        log_error(f"Failed to get email templates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve email templates"
        )

@router.post("/templates", response_model=EmailTemplateResponse)
async def create_email_template(
    template_data: EmailTemplateCreate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new email template."""
    try:
        new_template = EmailTemplate(**template_data.dict())
        db.add(new_template)
        await db.commit()
        await db.refresh(new_template)
        
        # Reload email service templates
        await fastapi_email_service.load_settings(db)
        
        log_info(f"Email template '{template_data.name}' created by {current_user.email}")
        return new_template
    except Exception as e:
        log_error(f"Failed to create email template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create email template"
        )

@router.put("/templates/{template_id}", response_model=EmailTemplateResponse)
async def update_email_template(
    template_id: int,
    template_data: EmailTemplateUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update email template."""
    try:
        result = await db.execute(
            select(EmailTemplate).where(EmailTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email template not found"
            )
        
        # Update fields
        update_data = template_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(template, field, value)
        
        await db.commit()
        await db.refresh(template)
        
        # Reload email service templates
        await fastapi_email_service.load_settings(db)
        
        log_info(f"Email template '{template.name}' updated by {current_user.email}")
        return template
    except Exception as e:
        log_error(f"Failed to update email template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update email template"
        )

@router.delete("/templates/{template_id}")
async def delete_email_template(
    template_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete email template."""
    try:
        result = await db.execute(
            select(EmailTemplate).where(EmailTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email template not found"
            )
        
        await db.delete(template)
        await db.commit()
        
        # Reload email service templates
        await fastapi_email_service.load_settings(db)
        
        log_info(f"Email template '{template.name}' deleted by {current_user.email}")
        return {"message": "Template deleted successfully"}
    except Exception as e:
        log_error(f"Failed to delete email template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete email template"
        )

# Email Sending Routes
@router.post("/send")
async def send_email(
    email_data: EmailSendRequest,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Send a single email."""
    try:
        await fastapi_email_service.load_settings(db)
        
        success = await fastapi_email_service.send_email(
            db=db,
            recipient_email=email_data.recipient_email,
            subject=email_data.subject,
            body=email_data.body,
            recipient_name=email_data.recipient_name,
            template_type=email_data.template_type
        )
        
        if success:
            log_info(f"Email sent to {email_data.recipient_email} by {current_user.email}")
            return {"success": True, "message": "Email sent successfully"}
        else:
            return {"success": False, "message": "Failed to send email"}
    except Exception as e:
        log_error(f"Failed to send email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}"
        )

@router.post("/send-bulk")
async def send_bulk_emails(
    email_data: EmailBulkSendRequest,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Send emails to multiple recipients."""
    try:
        await fastapi_email_service.load_settings(db)
        
        results = await fastapi_email_service.send_bulk_emails(
            db=db,
            recipient_emails=email_data.recipient_emails,
            recipient_names=email_data.recipient_names,
            subject=email_data.subject,
            body=email_data.body,
            template_type=email_data.template_type
        )
        
        log_info(f"Bulk email sent to {len(email_data.recipient_emails)} recipients by {current_user.email}")
        return results
    except Exception as e:
        log_error(f"Failed to send bulk emails: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send bulk emails: {str(e)}"
        )

@router.get("/users")
async def get_users_for_email(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all users for email selection."""
    try:
        result = await db.execute(
            select(User.id, User.name, User.email, User.designation, User.is_active)
            .where(User.is_active == True)
        )
        users = result.all()
        
        return [
            {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "designation": user.designation,
                "is_active": user.is_active
            }
            for user in users
        ]
    except Exception as e:
        log_error(f"Failed to get users for email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )

# Email Logs Routes
@router.get("/logs", response_model=PaginatedResponse)
async def get_email_logs(
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status_filter: Optional[str] = Query(None),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get email logs with pagination."""
    try:
        query = select(EmailLog)
        
        if status_filter:
            query = query.where(EmailLog.status == status_filter)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Get paginated results
        query = query.offset(offset).limit(limit).order_by(EmailLog.created_at.desc())
        result = await db.execute(query)
        logs = result.scalars().all()
        
        return {
            "items": [
                {
                    "id": log.id,
                    "recipient_email": log.recipient_email,
                    "recipient_name": log.recipient_name,
                    "subject": log.subject,
                    "template_type": log.template_type,
                    "status": log.status,
                    "error_message": log.error_message,
                    "sent_at": log.sent_at,
                    "created_at": log.created_at
                }
                for log in logs
            ],
            "total": total,
            "offset": offset,
            "limit": limit
        }
    except Exception as e:
        log_error(f"Failed to get email logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve email logs"
        )
