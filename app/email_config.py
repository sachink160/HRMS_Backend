"""
Email configuration using fastapi-mail
"""
from fastapi_mail import ConnectionConfig
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import EmailSettings
from app.database import get_db
import os

class EmailConfig:
    """Email configuration manager using fastapi-mail"""
    
    def __init__(self):
        self.config = None
        self.settings = None
    
    async def load_settings(self, db: AsyncSession) -> bool:
        """Load email settings from database and create fastapi-mail config"""
        try:
            result = await db.execute(
                select(EmailSettings).where(EmailSettings.is_active == True)
            )
            self.settings = result.scalar_one_or_none()
            
            if not self.settings:
                return False
            
            # Create fastapi-mail configuration
            import os
            template_folder = os.path.join(os.path.dirname(__file__), "..", "templates")
            
            self.config = ConnectionConfig(
                MAIL_USERNAME=self.settings.smtp_username,
                MAIL_PASSWORD=self.settings.smtp_password,
                MAIL_FROM=self.settings.from_email,
                MAIL_PORT=self.settings.smtp_port,
                MAIL_SERVER=self.settings.smtp_server,
                MAIL_FROM_NAME=self.settings.from_name,
                MAIL_STARTTLS=self.settings.smtp_use_tls,
                MAIL_SSL_TLS=self.settings.smtp_use_ssl,
                USE_CREDENTIALS=True,
                VALIDATE_CERTS=True,
                TEMPLATE_FOLDER=template_folder
            )
            
            return True
        except Exception as e:
            print(f"Failed to load email settings: {str(e)}")
            return False
    
    def get_config(self):
        """Get the fastapi-mail configuration"""
        return self.config
    
    def get_settings(self):
        """Get the email settings"""
        return self.settings

# Global email config instance
email_config = EmailConfig()
