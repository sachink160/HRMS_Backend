from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from app.models import UserRole, LeaveStatus

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    name: str
    phone: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None

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

class HolidayCreate(HolidayBase):
    pass

class HolidayUpdate(BaseModel):
    date: Optional[datetime] = None
    title: Optional[str] = None
    description: Optional[str] = None

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
