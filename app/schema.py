from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Union
from datetime import datetime, date
from app.models import UserRole, LeaveStatus, DocumentStatus

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    name: str
    phone: Optional[str] = None
    designation: Optional[str] = None
    joining_date: Optional[date] = None
    wifi_user_id: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    designation: Optional[str] = None
    joining_date: Optional[date] = None
    wifi_user_id: Optional[str] = None
    profile_image: Optional[str] = None
    aadhaar_front: Optional[str] = None
    aadhaar_back: Optional[str] = None
    pan_image: Optional[str] = None
    # When user updates a file, status will be set to pending in backend

class UserResponse(UserBase):
    id: int
    role: UserRole
    is_active: bool
    # Document paths
    profile_image: Optional[str] = None
    aadhaar_front: Optional[str] = None
    aadhaar_back: Optional[str] = None
    pan_image: Optional[str] = None
    # Document statuses
    profile_image_status: Optional[DocumentStatus] = None
    aadhaar_front_status: Optional[DocumentStatus] = None
    aadhaar_back_status: Optional[DocumentStatus] = None
    pan_image_status: Optional[DocumentStatus] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Leave Schemas
class LeaveBase(BaseModel):
    start_date: datetime
    end_date: datetime
    reason: str

class LeaveCreate(LeaveBase):
    pass

class LeaveUpdate(BaseModel):
    status: LeaveStatus

class LeaveResponse(LeaveBase):
    id: int
    user_id: int
    status: LeaveStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    user: Optional[UserResponse] = None
    
    class Config:
        from_attributes = True

# Holiday Schemas
class HolidayBase(BaseModel):
    date: datetime
    title: str
    description: Optional[str] = None
    is_active: bool = True

class HolidayCreate(BaseModel):
    date: Union[str, datetime]  # Accept both string and datetime
    title: str
    description: Optional[str] = None
    is_active: Optional[bool] = True
    
    @field_validator('date')
    @classmethod
    def validate_date(cls, v):
        if isinstance(v, str):
            try:
                # Try parsing as date string (YYYY-MM-DD)
                return datetime.fromisoformat(v)
            except ValueError:
                try:
                    # Try with time component
                    return datetime.fromisoformat(v + 'T00:00:00')
                except ValueError:
                    # Try parsing with different formats
                    from datetime import datetime
                    import re
                    
                    # Remove extra spaces and normalize
                    date_str = v.strip()
                    
                    # Handle different date formats
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
                    
                    for fmt in date_formats:
                        try:
                            parsed_date = datetime.strptime(date_str, fmt)
                            return parsed_date
                        except ValueError:
                            continue
                    
                    # Try parsing with different separators and order combinations
                    separators = ['-', '/', '.', ' ']
                    for sep in separators:
                        if sep in date_str:
                            parts = date_str.split(sep)
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
                                            return parsed_date
                                    except ValueError:
                                        continue
                    
                    raise ValueError(f"Invalid date format: {v}. Supported formats: YYYY-MM-DD, MM/DD/YYYY, DD/MM/YYYY, etc.")
        return v

class HolidayUpdate(BaseModel):
    date: Optional[Union[str, datetime]] = None  # Accept both string and datetime
    title: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    
    @field_validator('date')
    @classmethod
    def validate_date(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            try:
                # Try parsing as date string (YYYY-MM-DD)
                return datetime.fromisoformat(v)
            except ValueError:
                try:
                    # Try with time component
                    return datetime.fromisoformat(v + 'T00:00:00')
                except ValueError:
                    # Try parsing with different formats
                    from datetime import datetime
                    import re
                    
                    # Remove extra spaces and normalize
                    date_str = v.strip()
                    
                    # Handle different date formats
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
                    
                    for fmt in date_formats:
                        try:
                            parsed_date = datetime.strptime(date_str, fmt)
                            return parsed_date
                        except ValueError:
                            continue
                    
                    # Try parsing with different separators and order combinations
                    separators = ['-', '/', '.', ' ']
                    for sep in separators:
                        if sep in date_str:
                            parts = date_str.split(sep)
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
                                            return parsed_date
                                    except ValueError:
                                        continue
                    
                    raise ValueError(f"Invalid date format: {v}. Supported formats: YYYY-MM-DD, MM/DD/YYYY, DD/MM/YYYY, etc.")
        return v

class HolidayResponse(HolidayBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Tracker Schemas
class TrackerBase(BaseModel):
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    date: datetime

class TrackerCreate(TrackerBase):
    pass

class TrackerResponse(TrackerBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    user: Optional[UserResponse] = None
    
    class Config:
        from_attributes = True

# File Upload Schemas
class FileUploadResponse(BaseModel):
    filename: str
    file_path: str
    file_size: int
    content_type: str

# Email Settings Schemas
class EmailSettingsBase(BaseModel):
    smtp_server: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    from_email: str
    from_name: str
    is_active: bool = True

class EmailSettingsCreate(EmailSettingsBase):
    pass

class EmailSettingsUpdate(BaseModel):
    smtp_server: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: Optional[bool] = None
    smtp_use_ssl: Optional[bool] = None
    from_email: Optional[str] = None
    from_name: Optional[str] = None
    is_active: Optional[bool] = None

class EmailSettingsResponse(EmailSettingsBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Email Template Schemas
class EmailTemplateBase(BaseModel):
    name: str
    subject: str
    body: str
    template_type: str
    is_active: bool = True

class EmailTemplateCreate(EmailTemplateBase):
    pass

class EmailTemplateUpdate(BaseModel):
    name: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    template_type: Optional[str] = None
    is_active: Optional[bool] = None

class EmailTemplateResponse(EmailTemplateBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Email Sending Schemas
class EmailSendRequest(BaseModel):
    recipient_email: str
    recipient_name: Optional[str] = None
    subject: str
    body: str
    template_type: Optional[str] = None

class EmailBulkSendRequest(BaseModel):
    recipient_emails: List[str]
    recipient_names: Optional[List[str]] = None
    subject: str
    body: str
    template_type: Optional[str] = None

# Email Log Schemas
class EmailLogResponse(BaseModel):
    id: int
    recipient_email: str
    recipient_name: Optional[str] = None
    subject: str
    template_type: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Pagination Schema
class PaginationParams(BaseModel):
    offset: int = 0
    limit: int = 10

class PaginatedResponse(BaseModel):
    items: List[dict]
    total: int
    offset: int
    limit: int
