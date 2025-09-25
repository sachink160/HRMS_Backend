import aiosmtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from datetime import datetime
import logging
from jinja2 import Template

from app.models import EmailSettings, EmailLog, EmailTemplate
from app.logger import log_info, log_error

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.settings: Optional[EmailSettings] = None
        self.templates: dict = {}
    
    async def load_settings(self, db: AsyncSession) -> bool:
        """Load email settings from database."""
        try:
            result = await db.execute(
                select(EmailSettings).where(EmailSettings.is_active == True)
            )
            self.settings = result.scalar_one_or_none()
            
            if self.settings:
                log_info("Email settings loaded successfully")
                return True
            else:
                log_error("No active email settings found")
                return False
        except Exception as e:
            log_error(f"Failed to load email settings: {str(e)}")
            return False
    
    async def load_templates(self, db: AsyncSession) -> bool:
        """Load email templates from database."""
        try:
            result = await db.execute(
                select(EmailTemplate).where(EmailTemplate.is_active == True)
            )
            templates = result.scalars().all()
            
            self.templates = {template.template_type: template for template in templates}
            log_info(f"Loaded {len(templates)} email templates")
            return True
        except Exception as e:
            log_error(f"Failed to load email templates: {str(e)}")
            return False
    
    async def test_connection(self) -> bool:
        """Test SMTP connection with current settings."""
        if not self.settings:
            return False
        
        try:
            # Simplified approach - let aiosmtplib handle TLS automatically
            smtp = aiosmtplib.SMTP(
                hostname=self.settings.smtp_server,
                port=self.settings.smtp_port,
                use_tls=self.settings.smtp_use_tls and not self.settings.smtp_use_ssl
            )
            
            if self.settings.smtp_use_ssl:
                await smtp.connect(use_ssl=True)
            else:
                await smtp.connect()
            
            await smtp.login(self.settings.smtp_username, self.settings.smtp_password)
            await smtp.quit()
            
            log_info("SMTP connection test successful")
            return True
        except Exception as e:
            log_error(f"SMTP connection test failed: {str(e)}")
            return False
    
    def render_template(self, template_type: str, context: dict = None) -> tuple[str, str]:
        """Render email template with context variables."""
        if context is None:
            context = {}
        
        template = self.templates.get(template_type)
        if not template:
            raise ValueError(f"Template '{template_type}' not found")
        
        try:
            subject_template = Template(template.subject)
            body_template = Template(template.body)
            
            subject = subject_template.render(**context)
            body = body_template.render(**context)
            
            return subject, body
        except Exception as e:
            log_error(f"Template rendering failed: {str(e)}")
            raise
    
    async def send_email(
        self, 
        db: AsyncSession,
        recipient_email: str,
        subject: str,
        body: str,
        recipient_name: Optional[str] = None,
        template_type: Optional[str] = None
    ) -> bool:
        """Send a single email."""
        if not self.settings:
            log_error("Email settings not configured")
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
            message = MIMEMultipart()
            message['From'] = f"{self.settings.from_name} <{self.settings.from_email}>"
            message['To'] = recipient_email
            message['Subject'] = subject
            
            # Add body
            message.attach(MIMEText(body, 'html'))
            
            # Send email - simplified approach
            smtp = aiosmtplib.SMTP(
                hostname=self.settings.smtp_server,
                port=self.settings.smtp_port,
                use_tls=self.settings.smtp_use_tls and not self.settings.smtp_use_ssl
            )
            
            if self.settings.smtp_use_ssl:
                await smtp.connect(use_ssl=True)
            else:
                await smtp.connect()
            
            await smtp.login(self.settings.smtp_username, self.settings.smtp_password)
            await smtp.send_message(message)
            await smtp.quit()
            
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
        template_type: Optional[str] = None
    ) -> dict:
        """Send emails to multiple recipients."""
        results = {
            'total': len(recipient_emails),
            'sent': 0,
            'failed': 0,
            'errors': []
        }
        
        for email in recipient_emails:
            success = await self.send_email(
                db=db,
                recipient_email=email,
                subject=subject,
                body=body,
                template_type=template_type
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
        """Send email using a template."""
        try:
            subject, body = self.render_template(template_type, context)
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
email_service = EmailService()
