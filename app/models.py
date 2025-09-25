from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum, Date, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

Base = declarative_base()

class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class LeaveStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class DocumentStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    designation = Column(String, nullable=True)  # Employee designation/position
    joining_date = Column(Date, nullable=True)  # Employee joining date
    # External systems linkage
    wifi_user_id = Column(String, nullable=True, index=True)  # Optional WiFi portal user identifier
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Identity document fields
    profile_image = Column(String, nullable=True)  # Profile image file path
    aadhaar_front = Column(String, nullable=True)  # Aadhaar front image file path
    aadhaar_back = Column(String, nullable=True)  # Aadhaar back image file path
    pan_image = Column(String, nullable=True)  # PAN image file path
    
    # Identity document statuses
    profile_image_status = Column(Enum(DocumentStatus), default=DocumentStatus.PENDING, nullable=True)
    aadhaar_front_status = Column(Enum(DocumentStatus), default=DocumentStatus.PENDING, nullable=True)
    aadhaar_back_status = Column(Enum(DocumentStatus), default=DocumentStatus.PENDING, nullable=True)
    pan_image_status = Column(Enum(DocumentStatus), default=DocumentStatus.PENDING, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    leaves = relationship("Leave", back_populates="user")
    trackers = relationship("UserTracker", back_populates="user")
    
    # Database indexes for performance optimization
    __table_args__ = (
        Index('idx_user_role', 'role'),
        Index('idx_user_active', 'is_active'),
        Index('idx_user_created_at', 'created_at'),
        Index('idx_user_role_active', 'role', 'is_active'),
    )

class Leave(Base):
    __tablename__ = "leaves"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(Enum(LeaveStatus), default=LeaveStatus.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="leaves")
    
    # Database indexes for performance optimization
    __table_args__ = (
        Index('idx_leave_user_id', 'user_id'),
        Index('idx_leave_status', 'status'),
        Index('idx_leave_dates', 'start_date', 'end_date'),
        Index('idx_leave_user_status', 'user_id', 'status'),
        Index('idx_leave_created_at', 'created_at'),
        Index('idx_leave_user_created', 'user_id', 'created_at'),
    )

class Holiday(Base):
    __tablename__ = "holidays"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime(timezone=True), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Database indexes for performance optimization
    __table_args__ = (
        Index('idx_holiday_date', 'date'),
        Index('idx_holiday_active', 'is_active'),
        Index('idx_holiday_date_active', 'date', 'is_active'),
    )

class UserTracker(Base):
    __tablename__ = "user_trackers"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    check_in = Column(DateTime(timezone=True), nullable=True)
    check_out = Column(DateTime(timezone=True), nullable=True)
    date = Column(DateTime(timezone=True), nullable=False)  # The date this tracking record is for
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="trackers")
    
    # Database indexes for performance optimization
    __table_args__ = (
        Index('idx_tracker_user_id', 'user_id'),
        Index('idx_tracker_date', 'date'),
        Index('idx_tracker_user_date', 'user_id', 'date'),
        Index('idx_tracker_check_in', 'check_in'),
        Index('idx_tracker_user_checkin', 'user_id', 'check_in'),
    )

class EmailSettings(Base):
    __tablename__ = "email_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    smtp_server = Column(String, nullable=False)
    smtp_port = Column(Integer, nullable=False)
    smtp_username = Column(String, nullable=False)
    smtp_password = Column(String, nullable=False)  # Should be encrypted in production
    smtp_use_tls = Column(Boolean, default=True)
    smtp_use_ssl = Column(Boolean, default=False)
    from_email = Column(String, nullable=False)
    from_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Database indexes for performance optimization
    __table_args__ = (
        Index('idx_email_settings_active', 'is_active'),
    )

class EmailTemplate(Base):
    __tablename__ = "email_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    template_type = Column(String, nullable=False)  # e.g., 'welcome', 'leave_approval', 'leave_rejection', etc.
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Database indexes for performance optimization
    __table_args__ = (
        Index('idx_email_template_type', 'template_type'),
        Index('idx_email_template_active', 'is_active'),
    )

class EmailLog(Base):
    __tablename__ = "email_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    recipient_email = Column(String, nullable=False)
    recipient_name = Column(String, nullable=True)
    subject = Column(String, nullable=False)
    template_type = Column(String, nullable=True)
    status = Column(String, nullable=False)  # 'sent', 'failed', 'pending'
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Database indexes for performance optimization
    __table_args__ = (
        Index('idx_email_log_recipient', 'recipient_email'),
        Index('idx_email_log_status', 'status'),
        Index('idx_email_log_template', 'template_type'),
        Index('idx_email_log_created', 'created_at'),
    )
