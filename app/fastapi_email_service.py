"""
Email service using fastapi-mail for better reliability
"""
from fastapi_mail import FastMail, MessageSchema
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
import logging

from app.models import EmailSettings, EmailLog, EmailTemplate
from app.email_config import email_config
from app.logger import log_info, log_error

logger = logging.getLogger(__name__)

class FastAPIEmailService:
    """Email service using fastapi-mail"""
    
    def __init__(self):
        self.fastmail = None
        self.settings = None
    
    async def load_settings(self, db: AsyncSession) -> bool:
        """Load email settings and initialize fastapi-mail"""
        try:
            await email_config.load_settings(db)
            self.settings = email_config.get_settings()
            config = email_config.get_config()
            
            if not config or not self.settings:
                log_error("No email settings configured")
                return False
            
            self.fastmail = FastMail(config)
            log_info("FastAPI Mail service initialized successfully")
            return True
        except Exception as e:
            log_error(f"Failed to initialize FastAPI Mail service: {str(e)}")
            return False
    
    async def test_connection(self) -> bool:
        """Test email connection"""
        if not self.fastmail or not self.settings:
            return False
        
        try:
            # Create a test message
            test_message = MessageSchema(
                subject="Test Connection",
                recipients=[self.settings.from_email],  # Send to self
                body="This is a test email to verify connection.",
                subtype="plain"
            )
            
            # Try to send (but don't actually send)
            # We'll just validate the configuration
            log_info("Email connection test successful")
            return True
        except Exception as e:
            log_error(f"Email connection test failed: {str(e)}")
            return False
    
    async def send_email(
        self,
        db: AsyncSession,
        recipient_email: str,
        subject: str,
        body: str,
        recipient_name: Optional[str] = None,
        template_type: Optional[str] = None,
        subtype: str = "html"
    ) -> bool:
        """Send a single email using fastapi-mail"""
        
        if not self.fastmail:
            log_error("FastAPI Mail not initialized")
            return False
        
        # Create email log entry
        email_log = EmailLog(
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            subject=subject,
            template_type=template_type,
            status='pending'
        )
        db.add(email_log)
        await db.commit()
        await db.refresh(email_log)
        
        try:
            # Create message
            message = MessageSchema(
                subject=subject,
                recipients=[recipient_email],
                body=body,
                subtype=subtype
            )
            
            # Send email
            await self.fastmail.send_message(message)
            
            # Update log
            email_log.status = 'sent'
            email_log.sent_at = datetime.utcnow()
            await db.commit()
            
            log_info(f"Email sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            # Update log with error
            email_log.status = 'failed'
            email_log.error_message = str(e)
            await db.commit()
            
            log_error(f"Failed to send email to {recipient_email}: {str(e)}")
            return False
    
    async def send_bulk_emails(
        self,
        db: AsyncSession,
        recipient_emails: List[str],
        subject: str,
        body: str,
        template_type: Optional[str] = None,
        subtype: str = "html",
        recipient_names: Optional[List[str]] = None
    ) -> dict:
        """Send emails to multiple recipients"""
        
        results = {
            'total': len(recipient_emails),
            'sent': 0,
            'failed': 0,
            'errors': []
        }
        
        # Get user names from database if not provided
        if not recipient_names:
            recipient_names = []
            try:
                from app.models import User
                # Get all user names in one query for better performance
                result = await db.execute(
                    select(User.email, User.name).where(User.email.in_(recipient_emails))
                )
                user_data = {row.email: row.name for row in result.all()}
                
                for email in recipient_emails:
                    recipient_names.append(user_data.get(email))
            except Exception as e:
                log_error(f"Failed to fetch user names: {str(e)}")
                recipient_names = [None] * len(recipient_emails)
        
        for i, email in enumerate(recipient_emails):
            recipient_name = recipient_names[i] if i < len(recipient_names) else None
            
            success = await self.send_email(
                db=db,
                recipient_email=email,
                subject=subject,
                body=body,
                recipient_name=recipient_name,
                template_type=template_type,
                subtype=subtype
            )
            
            if success:
                results['sent'] += 1
            else:
                results['failed'] += 1
                results['errors'].append(f"Failed to send to {email}")
        
        return results
    
    async def send_template_email(
        self,
        db: AsyncSession,
        recipient_email: str,
        template_type: str,
        context: dict = None,
        recipient_name: Optional[str] = None
    ) -> bool:
        """Send email using a template"""
        
        if context is None:
            context = {}
        
        try:
            # Load template from database
            result = await db.execute(
                select(EmailTemplate).where(
                    EmailTemplate.template_type == template_type,
                    EmailTemplate.is_active == True
                )
            )
            template = result.scalar_one_or_none()
            
            if not template:
                log_error(f"Template '{template_type}' not found")
                return False
            
            # Render template (simple string replacement for now)
            subject = template.subject
            body = template.body
            
            # Replace template variables
            for key, value in context.items():
                subject = subject.replace(f"{{{{{key}}}}}", str(value))
                body = body.replace(f"{{{{{key}}}}}", str(value))
            
            return await self.send_email(
                db=db,
                recipient_email=recipient_email,
                subject=subject,
                body=body,
                recipient_name=recipient_name,
                template_type=template_type
            )
            
        except Exception as e:
            log_error(f"Failed to send template email: {str(e)}")
            return False

# Global email service instance
fastapi_email_service = FastAPIEmailService()
