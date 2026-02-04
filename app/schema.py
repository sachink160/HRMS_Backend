from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Union
from datetime import datetime, date, timezone
from decimal import Decimal
import enum
from app.models import UserRole, LeaveStatus, DocumentStatus, TaskStatus

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
    system_password: Optional[str] = None
    profile_image: Optional[str] = None
    aadhaar_front: Optional[str] = None
    aadhaar_back: Optional[str] = None
    pan_image: Optional[str] = None
    # When user updates a file, status will be set to pending in backend
    @field_validator('joining_date')
    @classmethod
    def validate_joining_date(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            # Try common date formats
            date_str = v.strip()
            for fmt in (
                '%Y-%m-%d',    # 2025-10-31
                '%d/%m/%Y',    # 31/10/2025
                '%m/%d/%Y',    # 10/31/2025
                '%d-%m-%Y',    # 31-10-2025
                '%m-%d-%Y',    # 10-31-2025
                '%Y/%m/%d',    # 2025/10/31
                '%d.%m.%Y',    # 31.10.2025
                '%m.%d.%Y',    # 10.31.2025
                '%Y.%m.%d',    # 2025.10.31
            ):
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
            # ISO strings like 2025-10-31T00:00:00
            try:
                return datetime.fromisoformat(date_str).date()
            except ValueError:
                pass
            raise ValueError(
                'Invalid joining_date format. Use YYYY-MM-DD or common local formats.'
            )
        return v

class AdminUserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    designation: Optional[str] = None
    joining_date: Optional[date] = None
    wifi_user_id: Optional[str] = None
    role: Optional[UserRole] = None
    profile_image: Optional[str] = None
    aadhaar_front: Optional[str] = None
    aadhaar_back: Optional[str] = None
    pan_image: Optional[str] = None
    
    # Employee details
    employee_id: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    nationality: Optional[str] = None
    personal_email: Optional[str] = None
    company_email: Optional[str] = None
    company_email_password: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    current_address: Optional[str] = None
    permanent_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    department: Optional[str] = None
    manager_id: Optional[int] = None
    employment_type: Optional[str] = None
    work_location: Optional[str] = None
    work_schedule: Optional[str] = None
    basic_salary: Optional[str] = None
    currency: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    skills: Optional[str] = None
    certifications: Optional[str] = None
    education_qualification: Optional[str] = None
    previous_experience_years: Optional[int] = None
    
    # Probation details
    probation_period_months: Optional[int] = None
    probation_start_date: Optional[date] = None
    probation_end_date: Optional[date] = None
    probation_status: Optional[str] = None
    probation_review_date: Optional[date] = None
    probation_review_notes: Optional[str] = None
    probation_reviewer_id: Optional[int] = None
    
    # Termination details
    termination_date: Optional[date] = None
    termination_reason: Optional[str] = None
    termination_type: Optional[str] = None
    termination_notice_period_days: Optional[int] = None
    last_working_date: Optional[date] = None
    termination_notes: Optional[str] = None
    termination_initiated_by: Optional[int] = None
    exit_interview_date: Optional[date] = None
    exit_interview_notes: Optional[str] = None
    clearance_status: Optional[str] = None
    final_settlement_amount: Optional[str] = None
    final_settlement_date: Optional[date] = None
    
    # Assets & Security
    hardware_allocation: Optional[str] = None
    system_password: Optional[str] = None
    
    # When admin updates a file, status will be set to pending in backend
    @field_validator('joining_date')
    @classmethod
    def validate_joining_date(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            # Try common date formats
            date_str = v.strip()
            for fmt in (
                '%Y-%m-%d',    # 2025-10-31
                '%d/%m/%Y',    # 31/10/2025
                '%m/%d/%Y',    # 10/31/2025
                '%d-%m-%Y',    # 31-10-2025
                '%m-%d-%Y',    # 10-31-2025
                '%Y/%m/%d',    # 2025/10/31
                '%d.%m.%Y',    # 31.10.2025
                '%m.%d.%Y',    # 10.31.2025
                '%Y.%m.%d',    # 2025.10.31
            ):
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
            # ISO strings like 2025-10-31T00:00:00
            try:
                return datetime.fromisoformat(date_str).date()
            except ValueError:
                pass
            raise ValueError(
                'Invalid joining_date format. Use YYYY-MM-DD or common local formats.'
            )
        return v

class PasswordChange(BaseModel):
    """Schema for password change request."""
    current_password: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class AdminPasswordReset(BaseModel):
    """Schema for admin to reset user password without requiring current password."""
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

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
    # Employee details
    employee_id: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    nationality: Optional[str] = None
    personal_email: Optional[str] = None
    company_email: Optional[str] = None
    company_email_password: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    current_address: Optional[str] = None
    permanent_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    department: Optional[str] = None
    manager_id: Optional[int] = None
    employment_type: Optional[str] = None
    work_location: Optional[str] = None
    work_schedule: Optional[str] = None
    basic_salary: Optional[str] = None
    currency: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    skills: Optional[str] = None
    certifications: Optional[str] = None
    education_qualification: Optional[str] = None
    previous_experience_years: Optional[int] = None
    
    # Probation details
    probation_period_months: Optional[int] = None
    probation_start_date: Optional[date] = None
    probation_end_date: Optional[date] = None
    probation_status: Optional[str] = None
    probation_review_date: Optional[date] = None
    probation_review_notes: Optional[str] = None
    probation_reviewer_id: Optional[int] = None
    
    # Termination details
    termination_date: Optional[date] = None
    termination_reason: Optional[str] = None
    termination_type: Optional[str] = None
    termination_notice_period_days: Optional[int] = None
    last_working_date: Optional[date] = None
    termination_notes: Optional[str] = None
    termination_initiated_by: Optional[int] = None
    exit_interview_date: Optional[date] = None
    exit_interview_notes: Optional[str] = None
    clearance_status: Optional[str] = None
    final_settlement_amount: Optional[str] = None
    final_settlement_date: Optional[date] = None
    
    # Assets & Security
    hardware_allocation: Optional[str] = None
    system_password: Optional[str] = None
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

# Admin Creation with Secret Code Schema
class AdminCreateWithSecret(UserBase):
    password: str
    secret_code: str
    role: UserRole  # "admin"

# Leave Schemas
class LeaveBase(BaseModel):
    start_date: Union[str, datetime]  # Accept both string and datetime
    end_date: Union[str, datetime]    # Accept both string and datetime
    total_days: Union[int, float, Decimal]  # Supports decimal values like 4.5 for half-days
    reason: str

class LeaveCreate(LeaveBase):
    @field_validator('total_days')
    @classmethod
    def validate_total_days(cls, v):
        """Validate total_days to support half-days (0.5 increments)"""
        if isinstance(v, (int, float, Decimal)):
            # Convert to float for validation
            days = float(v)
            
            # Check if it's a positive number
            if days <= 0:
                raise ValueError("Total days must be greater than 0")
            
            # Check if it's a valid half-day increment (0.5, 1.0, 1.5, 2.0, etc.)
            if days * 2 != int(days * 2):
                raise ValueError("Total days must be in 0.5 increments (e.g., 1.0, 1.5, 2.0, 2.5)")
            
            return days
        else:
            raise ValueError("Total days must be a number")
    
    @field_validator('start_date')
    @classmethod
    def validate_start_date(cls, v):
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
                    
                    raise ValueError(f"Invalid start_date format: {v}. Supported formats: YYYY-MM-DD, MM/DD/YYYY, DD/MM/YYYY, etc.")
        
        # Ensure the datetime is timezone-aware
        if isinstance(v, datetime) and v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v

    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v):
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
                    
                    raise ValueError(f"Invalid end_date format: {v}. Supported formats: YYYY-MM-DD, MM/DD/YYYY, DD/MM/YYYY, etc.")
        
        # Ensure the datetime is timezone-aware
        if isinstance(v, datetime) and v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v

class LeaveUpdate(BaseModel):
    start_date: Optional[Union[str, datetime]] = None
    end_date: Optional[Union[str, datetime]] = None
    total_days: Optional[Union[int, float, Decimal]] = None
    reason: Optional[str] = None
    status: Optional[LeaveStatus] = None  # For admin status updates
    
    @field_validator('total_days')
    @classmethod
    def validate_total_days(cls, v):
        """Validate total_days to support half-days (0.5 increments)"""
        if v is not None:
            if isinstance(v, (int, float, Decimal)):
                # Convert to float for validation
                days = float(v)
                
                # Check if it's a positive number
                if days <= 0:
                    raise ValueError("Total days must be greater than 0")
                
                # Check if it's a valid half-day increment (0.5, 1.0, 1.5, 2.0, etc.)
                if days * 2 != int(days * 2):
                    raise ValueError("Total days must be in 0.5 increments (e.g., 1.0, 1.5, 2.0, 2.5)")
                
                return days
            else:
                raise ValueError("Total days must be a number")
        return v
    
    @field_validator('start_date')
    @classmethod
    def validate_start_date(cls, v):
        if v is not None:
            if isinstance(v, str):
                try:
                    # Try parsing as ISO format datetime string
                    parsed = datetime.fromisoformat(v.replace('Z', '+00:00'))
                    # Ensure timezone-aware
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=timezone.utc)
                    return parsed
                except ValueError:
                    try:
                        # Try with time component
                        parsed = datetime.fromisoformat(v + 'T00:00:00')
                        if parsed.tzinfo is None:
                            parsed = parsed.replace(tzinfo=timezone.utc)
                        return parsed
                    except ValueError:
                        # Try parsing with different formats
                        date_str = v.strip()
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
                                parsed = datetime.strptime(date_str, fmt)
                                parsed = parsed.replace(tzinfo=timezone.utc)
                                return parsed
                            except ValueError:
                                continue
                        
                        raise ValueError(f"Invalid start_date format: {v}. Supported formats: YYYY-MM-DD, YYYY-MM-DDTHH:MM:SS, etc.")
            elif isinstance(v, datetime):
                # Ensure timezone-aware
                if v.tzinfo is None:
                    v = v.replace(tzinfo=timezone.utc)
                return v
        return v
    
    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v):
        if v is not None:
            if isinstance(v, str):
                try:
                    # Try parsing as ISO format datetime string
                    parsed = datetime.fromisoformat(v.replace('Z', '+00:00'))
                    # Ensure timezone-aware
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=timezone.utc)
                    return parsed
                except ValueError:
                    try:
                        # Try with time component
                        parsed = datetime.fromisoformat(v + 'T23:59:59')
                        if parsed.tzinfo is None:
                            parsed = parsed.replace(tzinfo=timezone.utc)
                        return parsed
                    except ValueError:
                        # Try parsing with different formats
                        date_str = v.strip()
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
                                parsed = datetime.strptime(date_str, fmt)
                                parsed = parsed.replace(tzinfo=timezone.utc)
                                return parsed
                            except ValueError:
                                continue
                        
                        raise ValueError(f"Invalid end_date format: {v}. Supported formats: YYYY-MM-DD, YYYY-MM-DDTHH:MM:SS, etc.")
            elif isinstance(v, datetime):
                # Ensure timezone-aware
                if v.tzinfo is None:
                    v = v.replace(tzinfo=timezone.utc)
                return v
        return v

class LeaveResponse(BaseModel):
    id: int
    user_id: int
    start_date: datetime
    end_date: datetime
    total_days: Union[int, float, Decimal]  # Supports decimal values like 4.5 for half-days
    reason: str
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
class PausePeriod(BaseModel):
    """
    Represents a single break interval within a working day.

    NOTE:
    - The API expects ISO 8601 datetimes for both fields.
    - When no timezone offset is provided, values are interpreted in the
      application's business timezone (IST / Asia-Kolkata) and normalised
      to timezone-aware datetimes on the server.
    - For time-correction requests we always expect a *closed* interval
      (i.e. pause_end is provided) so that work duration can be recalculated
      deterministically.
    """
    pause_start: datetime
    pause_end: Optional[datetime] = None

class TrackerBase(BaseModel):
    date: Optional[date] = None
    clock_in: Optional[datetime] = None
    clock_out: Optional[datetime] = None

class TrackerCreate(BaseModel):
    pass  # Clock in/out handled by endpoints

class TrackerResponse(BaseModel):
    id: int
    user_id: int
    date: date
    clock_in: datetime
    clock_out: Optional[datetime] = None
    status: str
    pause_periods: Optional[List[PausePeriod]] = None
    total_work_seconds: Optional[int] = None
    total_pause_seconds: Optional[int] = None
    total_work_hours: Optional[float] = None  # Calculated field
    created_at: datetime
    updated_at: Optional[datetime] = None
    user: Optional[UserResponse] = None
    
    class Config:
        from_attributes = True

class TrackerCurrentResponse(BaseModel):
    """Response for current active/paused session"""
    has_active_session: bool
    tracker: Optional[TrackerResponse] = None
    current_work_seconds: Optional[int] = None  # Current elapsed time excluding pauses
    current_pause_seconds: Optional[int] = None  # Current paused time if paused

class TrackerSummaryResponse(BaseModel):
    """Summary for admin reports"""
    user_id: int
    user_name: str
    user_email: str
    date: date
    clock_in: Optional[datetime] = None
    clock_out: Optional[datetime] = None
    total_work_hours: float
    status: str

class DurationHMS(BaseModel):
    """Hours/minutes/seconds breakdown."""
    hours: int
    minutes: int
    seconds: int

class TrackerDailyHours(BaseModel):
    """Per-day aggregation for hours charts."""
    date: date
    total_work_seconds: int
    total_work_hours: float
    total_work_hms: DurationHMS

class TrackerHoursSummary(BaseModel):
    """Aggregate hours summary within a date range."""
    total_work_seconds: int
    total_work_hours: float
    days_worked: int
    avg_daily_hours: float
    total_work_hms: DurationHMS
    avg_daily_hms: DurationHMS

class TrackerUserHours(BaseModel):
    """Aggregate hours per user for admin dashboard tables."""
    user_id: int
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    total_work_seconds: int
    total_work_hours: float
    days_worked: int
    avg_daily_hours: float
    total_work_hms: DurationHMS
    avg_daily_hms: DurationHMS

class TrackerHoursResponse(BaseModel):
    """Hours summary plus per-day breakdown."""
    date_range_start: date
    date_range_end: date
    user_id: Optional[int] = None
    summary: TrackerHoursSummary
    daily: List[TrackerDailyHours]

class TrackerHoursByUserResponse(BaseModel):
    """Aggregated hours grouped by user."""
    date_range_start: date
    date_range_end: date
    items: List[TrackerUserHours]

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

# Employee Details Schemas
class EmployeeDetailsBase(BaseModel):
    employee_id: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    nationality: Optional[str] = None
    personal_email: Optional[str] = None
    company_email: Optional[str] = None
    company_email_password: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    current_address: Optional[str] = None
    permanent_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    department: Optional[str] = None
    manager_id: Optional[int] = None
    employment_type: Optional[str] = None
    work_location: Optional[str] = None
    work_schedule: Optional[str] = None
    basic_salary: Optional[str] = None
    currency: Optional[str] = "INR"
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    skills: Optional[str] = None  # JSON string
    certifications: Optional[str] = None  # JSON string
    education_qualification: Optional[str] = None
    previous_experience_years: Optional[int] = None
    
    # Probation Management (exposed in responses)
    probation_period_months: Optional[int] = None
    probation_start_date: Optional[date] = None
    probation_end_date: Optional[date] = None
    probation_status: Optional[str] = None
    probation_review_date: Optional[date] = None
    probation_review_notes: Optional[str] = None
    probation_reviewer_id: Optional[int] = None
    
    # Termination Management (exposed in responses)
    termination_date: Optional[date] = None
    termination_reason: Optional[str] = None
    termination_type: Optional[str] = None
    termination_notice_period_days: Optional[int] = None
    last_working_date: Optional[date] = None
    termination_notes: Optional[str] = None
    termination_initiated_by: Optional[int] = None
    exit_interview_date: Optional[date] = None
    exit_interview_notes: Optional[str] = None
    clearance_status: Optional[str] = None
    final_settlement_amount: Optional[str] = None
    final_settlement_date: Optional[date] = None

class EmployeeDetailsCreate(EmployeeDetailsBase):
    user_id: int

class EmployeeDetailsUpdate(BaseModel):
    employee_id: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    nationality: Optional[str] = None
    personal_email: Optional[str] = None
    company_email: Optional[str] = None
    company_email_password: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    current_address: Optional[str] = None
    permanent_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    department: Optional[str] = None
    manager_id: Optional[int] = None
    employment_type: Optional[str] = None
    work_location: Optional[str] = None
    work_schedule: Optional[str] = None
    basic_salary: Optional[str] = None
    currency: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    skills: Optional[str] = None
    certifications: Optional[str] = None
    education_qualification: Optional[str] = None
    previous_experience_years: Optional[int] = None
    
    # Probation Management
    probation_period_months: Optional[int] = None
    probation_start_date: Optional[date] = None
    probation_end_date: Optional[date] = None
    probation_status: Optional[str] = None
    probation_review_date: Optional[date] = None
    probation_review_notes: Optional[str] = None
    probation_reviewer_id: Optional[int] = None
    
    # Termination Management
    termination_date: Optional[date] = None
    termination_reason: Optional[str] = None
    termination_type: Optional[str] = None
    termination_notice_period_days: Optional[int] = None
    last_working_date: Optional[date] = None
    termination_notes: Optional[str] = None
    termination_initiated_by: Optional[int] = None
    exit_interview_date: Optional[date] = None
    exit_interview_notes: Optional[str] = None
    clearance_status: Optional[str] = None
    final_settlement_amount: Optional[str] = None
    final_settlement_date: Optional[date] = None

class EmployeeDetailsResponse(EmployeeDetailsBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    user: Optional[UserResponse] = None
    manager: Optional[UserResponse] = None
    probation_reviewer: Optional[UserResponse] = None
    termination_initiator: Optional[UserResponse] = None
    
    class Config:
        from_attributes = True

# Probation Management Schemas
class ProbationReviewCreate(BaseModel):
    probation_status: str  # passed, failed, extended
    probation_review_date: date
    probation_review_notes: Optional[str] = None
    probation_reviewer_id: int

class ProbationReviewUpdate(BaseModel):
    probation_status: Optional[str] = None
    probation_review_date: Optional[date] = None
    probation_review_notes: Optional[str] = None
    probation_reviewer_id: Optional[int] = None

class ProbationExtensionCreate(BaseModel):
    extension_months: int
    extension_reason: str
    probation_reviewer_id: int

# Termination Management Schemas
class TerminationCreate(BaseModel):
    termination_date: date
    termination_reason: str
    termination_type: str  # voluntary, involuntary, retirement
    termination_notice_period_days: Optional[int] = None
    last_working_date: Optional[date] = None
    termination_notes: Optional[str] = None
    termination_initiated_by: int

class TerminationUpdate(BaseModel):
    termination_date: Optional[date] = None
    termination_reason: Optional[str] = None
    termination_type: Optional[str] = None
    termination_notice_period_days: Optional[int] = None
    last_working_date: Optional[date] = None
    termination_notes: Optional[str] = None
    termination_initiated_by: Optional[int] = None
    exit_interview_date: Optional[date] = None
    exit_interview_notes: Optional[str] = None
    clearance_status: Optional[str] = None
    final_settlement_amount: Optional[str] = None
    final_settlement_date: Optional[date] = None

# Employment History Schemas
class EmploymentHistoryBase(BaseModel):
    position_title: str
    department: Optional[str] = None
    employment_type: Optional[str] = None
    work_location: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    salary: Optional[str] = None
    currency: Optional[str] = "INR"
    manager_id: Optional[int] = None
    reporting_manager_name: Optional[str] = None
    status: Optional[str] = None
    reason_for_change: Optional[str] = None
    notes: Optional[str] = None

class EmploymentHistoryCreate(EmploymentHistoryBase):
    user_id: int

class EmploymentHistoryUpdate(BaseModel):
    position_title: Optional[str] = None
    department: Optional[str] = None
    employment_type: Optional[str] = None
    work_location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    salary: Optional[str] = None
    currency: Optional[str] = None
    manager_id: Optional[int] = None
    reporting_manager_name: Optional[str] = None
    status: Optional[str] = None
    reason_for_change: Optional[str] = None
    notes: Optional[str] = None
    is_current: Optional[bool] = None

class EmploymentHistoryResponse(EmploymentHistoryBase):
    id: int
    user_id: int
    is_current: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    user: Optional[UserResponse] = None
    manager: Optional[UserResponse] = None
    
    class Config:
        from_attributes = True

# Enhanced Tracker Response with Employee Details
class EnhancedTrackerResponse(TrackerResponse):
    employee_details: Optional[EmployeeDetailsResponse] = None
    current_position: Optional[EmploymentHistoryResponse] = None

# Employee Summary Schema
class EmployeeSummary(BaseModel):
    user: UserResponse
    employee_details: Optional[UserResponse] = None
    current_position: Optional[EmploymentHistoryResponse] = None
    recent_tracking: List[TrackerResponse] = []
    total_work_days: Optional[int] = None
    average_hours_per_day: Optional[float] = None

# Pagination Schema
class PaginationParams(BaseModel):
    offset: int = 0
    limit: int = 10

class PaginatedResponse(BaseModel):
    items: List[dict]
    total: int
    offset: int
    limit: int

# Task Schemas
class TaskBase(BaseModel):
    name: str
    description: Optional[str] = None
    due_date: Optional[Union[str, datetime]] = None
    priority: Optional[str] = "medium"  # low, medium, high, urgent
    category: Optional[str] = None

class TaskCreate(TaskBase):
    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v):
        if v is not None and isinstance(v, str):
            try:
                # Try parsing as date string (YYYY-MM-DD)
                return datetime.fromisoformat(v)
            except ValueError:
                try:
                    # Try with time component
                    return datetime.fromisoformat(v + 'T00:00:00')
                except ValueError:
                    try:
                        # Try parsing with different formats
                        date_str = v.strip()
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
                        
                        raise ValueError(f"Invalid due_date format: {v}. Supported formats: YYYY-MM-DD, MM/DD/YYYY, DD/MM/YYYY, etc.")
                    except Exception:
                        raise ValueError(f"Invalid due_date format: {v}")
        
        # Ensure the datetime is timezone-aware
        if isinstance(v, datetime) and v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v

class TaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    due_date: Optional[Union[str, datetime]] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    
    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v):
        if v is not None and isinstance(v, str):
            try:
                return datetime.fromisoformat(v)
            except ValueError:
                try:
                    return datetime.fromisoformat(v + 'T00:00:00')
                except ValueError:
                    raise ValueError("Invalid due date format")
        return v

class TaskResponse(TaskBase):
    id: int
    user_id: int
    status: TaskStatus
    completed_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    user: Optional[UserResponse] = None
    
    class Config:
        from_attributes = True

# Task Summary Schema
class TaskSummary(BaseModel):
    total_tasks: int
    pending_tasks: int
    in_progress_tasks: int
    completed_tasks: int
    cancelled_tasks: int
    overdue_tasks: int

# Password Reset Schemas
class ForgotPasswordRequest(BaseModel):
    """Request password reset email."""
    email: EmailStr

class VerifyResetTokenResponse(BaseModel):
    """Response for token verification."""
    valid: bool
    message: str

class ResetPasswordRequest(BaseModel):
    """Reset password with token."""
    token: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v



# Time Correction Request Schemas
class TimeCorrectionRequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class TimeCorrectionRequestCreate(BaseModel):
    request_date: Union[str, date]
    issue_type: str  # missed_clock_in, missed_clock_out, wrong_time, forgot_clock_out, forgot_resume
    
    requested_clock_in: Optional[Union[str, datetime]] = None
    requested_clock_out: Optional[Union[str, datetime]] = None
    # When provided as a list from the client, this is a list of PausePeriod
    # objects (each with pause_start and pause_end datetimes). The validator
    # below will convert the list into a JSON string that is stored as-is on
    # the TimeCorrectionRequest model for later use during approval.
    requested_pause_periods: Optional[Union[List[PausePeriod], str]] = None
    
    reason: str
    
    @field_validator('request_date')
    @classmethod
    def validate_request_date(cls, v):
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v).date()
            except ValueError:
                # Try common formats
                try:
                    return datetime.strptime(v, '%Y-%m-%d').date()
                except ValueError:
                    raise ValueError("Invalid request_date format")
        return v
    
    @field_validator('requested_clock_in', 'requested_clock_out')
    @classmethod
    def validate_times(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            try:
                dt = datetime.fromisoformat(v.replace('Z', '+00:00'))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                raise ValueError(f"Invalid datetime format: {v}")
        if isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    @field_validator('requested_pause_periods')
    @classmethod
    def validate_pause_periods(cls, v):
        if v is None:
            return None
        if isinstance(v, list):
            import json
            # Verify list items are PausePeriod or dicts
            return json.dumps([p.model_dump() if hasattr(p, 'model_dump') else p for p in v], default=str)
        if isinstance(v, str):
            # Evaluate if it's valid JSON
            import json
            try:
                json.loads(v)
                return v
            except ValueError:
                raise ValueError("Invalid JSON string for pause periods")
        return v

class TimeCorrectionRequestUpdate(BaseModel):
    status: Optional[TimeCorrectionRequestStatus] = None
    admin_notes: Optional[str] = None

class TimeCorrectionLogResponse(BaseModel):
    id: int
    request_id: int
    action: str
    performed_by: int
    old_values: Optional[str] = None
    new_values: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    performer: Optional[UserResponse] = None
    
    class Config:
        from_attributes = True

class TimeCorrectionRequestResponse(BaseModel):
    id: int
    user_id: int
    tracker_id: Optional[int] = None
    request_date: date
    issue_type: str
    
    current_clock_in: Optional[datetime] = None
    current_clock_out: Optional[datetime] = None
    requested_clock_in: Optional[datetime] = None
    requested_clock_out: Optional[datetime] = None
    
    current_pause_periods: Optional[str] = None
    requested_pause_periods: Optional[str] = None
    
    reason: str
    status: TimeCorrectionRequestStatus
    
    admin_notes: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    user: Optional[UserResponse] = None
    reviewer: Optional[UserResponse] = None
    logs: Optional[List[TimeCorrectionLogResponse]] = None
    
    class Config:
        from_attributes = True
