from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Union
from datetime import datetime, date
from app.models import UserRole, LeaveStatus

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    name: str
    phone: Optional[str] = None
    designation: Optional[str] = None
    joining_date: Optional[date] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    designation: Optional[str] = None
    joining_date: Optional[date] = None

class UserResponse(UserBase):
    id: int
    role: UserRole
    is_active: bool
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
                    raise ValueError(f"Invalid date format: {v}. Expected YYYY-MM-DD format.")
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
                    raise ValueError(f"Invalid date format: {v}. Expected YYYY-MM-DD format.")
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

# Pagination Schema
class PaginationParams(BaseModel):
    offset: int = 0
    limit: int = 10

class PaginatedResponse(BaseModel):
    items: List[dict]
    total: int
    offset: int
    limit: int
