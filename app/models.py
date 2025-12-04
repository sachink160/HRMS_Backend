from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum, Date, Index, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

Base = declarative_base()

class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"

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

    # BEGIN merged EmployeeDetails fields
    # Personal Information
    employee_id = Column(String, nullable=True, unique=True, index=True)  # Company employee ID
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String, nullable=True)
    marital_status = Column(String, nullable=True)
    nationality = Column(String, nullable=True)
    
    # Contact Information
    personal_email = Column(String, nullable=True)
    company_email = Column(String, nullable=True, index=True)  # Company email address
    company_email_password = Column(String, nullable=True)  # Company email password (should be encrypted in production)
    # IT Assets & Credentials
    hardware_allocation = Column(Text, nullable=True)  # Details of allocated hardware (e.g., laptop, accessories)
    system_password = Column(String, nullable=True)  # System password (should be encrypted in production)
    emergency_contact_name = Column(String, nullable=True)
    emergency_contact_phone = Column(String, nullable=True)
    emergency_contact_relation = Column(String, nullable=True)
    
    # Address Information
    current_address = Column(Text, nullable=True)
    permanent_address = Column(Text, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    country = Column(String, nullable=True)
    
    # Professional Information
    department = Column(String, nullable=True)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    employment_type = Column(String, nullable=True)  # Full-time, Part-time, Contract, Intern
    work_location = Column(String, nullable=True)
    work_schedule = Column(String, nullable=True)  # Regular hours, Shift work, etc.
    
    # Financial Information
    basic_salary = Column(String, nullable=True)  # Store as string to handle different currencies
    currency = Column(String, nullable=True, default="INR")
    bank_name = Column(String, nullable=True)
    bank_account_number = Column(String, nullable=True)
    ifsc_code = Column(String, nullable=True)
    
    # Skills and Qualifications
    skills = Column(Text, nullable=True)  # JSON string of skills
    certifications = Column(Text, nullable=True)  # JSON string of certifications
    education_qualification = Column(String, nullable=True)
    previous_experience_years = Column(Integer, nullable=True)
    
    # Probation Management
    probation_period_months = Column(Integer, nullable=True, default=6)  # Default 6 months
    probation_start_date = Column(Date, nullable=True)
    probation_end_date = Column(Date, nullable=True)
    probation_status = Column(String, nullable=True, default="pending")  # pending, passed, failed, extended
    probation_review_date = Column(Date, nullable=True)
    probation_review_notes = Column(Text, nullable=True)
    probation_reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Termination Management
    termination_date = Column(Date, nullable=True)
    termination_reason = Column(String, nullable=True)  # resignation, dismissal, retirement, etc.
    termination_type = Column(String, nullable=True)  # voluntary, involuntary, retirement
    termination_notice_period_days = Column(Integer, nullable=True)
    last_working_date = Column(Date, nullable=True)
    termination_notes = Column(Text, nullable=True)
    termination_initiated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    exit_interview_date = Column(Date, nullable=True)
    exit_interview_notes = Column(Text, nullable=True)
    clearance_status = Column(String, nullable=True, default="pending")  # pending, completed
    final_settlement_amount = Column(String, nullable=True)
    final_settlement_date = Column(Date, nullable=True)
    # END merged EmployeeDetails fields
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    leaves = relationship("Leave", back_populates="user")
    manager = relationship("User", remote_side=[id], backref="managed_employees", foreign_keys=[manager_id])
    probation_reviewer = relationship("User", remote_side=[id], backref="probation_reviews", foreign_keys=[probation_reviewer_id])
    termination_initiator = relationship("User", remote_side=[id], backref="termination_initiated", foreign_keys=[termination_initiated_by])
    
    # Database indexes for performance optimization
    __table_args__ = (
        Index('idx_user_role', 'role'),
        Index('idx_user_active', 'is_active'),
        Index('idx_user_created_at', 'created_at'),
        Index('idx_user_role_active', 'role', 'is_active'),
        Index('idx_user_department', 'department'),
        Index('idx_user_manager', 'manager_id'),
        Index('idx_user_probation_status', 'probation_status'),
        Index('idx_user_probation_end_date', 'probation_end_date'),
        Index('idx_user_termination_date', 'termination_date'),
        Index('idx_user_clearance_status', 'clearance_status'),
    )

class Leave(Base):
    __tablename__ = "leaves"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    total_days = Column(Numeric(4, 1), nullable=False)  # Supports decimal values like 4.5 for half-days
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


class EmploymentHistory(Base):
    __tablename__ = "employment_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Position Information
    position_title = Column(String, nullable=False)
    department = Column(String, nullable=True)
    employment_type = Column(String, nullable=True)  # Full-time, Part-time, Contract, Intern
    work_location = Column(String, nullable=True)
    
    # Dates
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)  # NULL for current position
    
    # Compensation
    salary = Column(String, nullable=True)  # Store as string to handle different currencies
    currency = Column(String, nullable=True, default="INR")
    
    # Reporting Structure
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reporting_manager_name = Column(String, nullable=True)
    
    # Status and Notes
    status = Column(String, nullable=True)  # Active, Promoted, Transferred, Resigned, etc.
    reason_for_change = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # System Information
    is_current = Column(Boolean, default=False)  # True for current position
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="employment_history")
    manager = relationship("User", foreign_keys=[manager_id], backref="managed_history")
    
    # Database indexes for performance optimization
    __table_args__ = (
        Index('idx_employment_user_id', 'user_id'),
        Index('idx_employment_position', 'position_title'),
        Index('idx_employment_department', 'department'),
        Index('idx_employment_dates', 'start_date', 'end_date'),
        Index('idx_employment_current', 'is_current'),
        Index('idx_employment_manager', 'manager_id'),
        Index('idx_employment_created_at', 'created_at'),
    )

class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Task Information
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    
    # Task Dates
    due_date = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Priority and Category
    priority = Column(String, nullable=True, default="medium")  # low, medium, high, urgent
    category = Column(String, nullable=True)  # work, personal, project, etc.
    
    # System Information
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref="tasks")
    
    # Database indexes for performance optimization
    __table_args__ = (
        Index('idx_task_user_id', 'user_id'),
        Index('idx_task_status', 'status'),
        Index('idx_task_priority', 'priority'),
        Index('idx_task_category', 'category'),
        Index('idx_task_due_date', 'due_date'),
        Index('idx_task_active', 'is_active'),
        Index('idx_task_created_at', 'created_at'),
        Index('idx_task_user_status', 'user_id', 'status'),
        Index('idx_task_user_created', 'user_id', 'created_at'),
    )

class TimeLogStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"  # Timer is running
    PAUSED = "PAUSED"  # Timer is paused (can be resumed)
    ON_BREAK = "ON_BREAK"  # Currently on break
    COMPLETED = "COMPLETED"  # Timer stopped for the day (clocked out)

class TimeLog(Base):
    __tablename__ = "time_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Date for this time log entry
    log_date = Column(Date, nullable=False)
    
    # Start and end times
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    
    # Break tracking (stored as JSON string: [{"start": "...", "end": "..."}, ...])
    breaks = Column(Text, nullable=True)  # JSON array of break objects
    
    # Calculated durations (in seconds)
    total_break_duration = Column(Integer, default=0, nullable=False)  # Total break time in seconds
    total_work_duration = Column(Integer, nullable=True)  # Total work time in seconds (excluding breaks)
    
    # Status
    status = Column(Enum(TimeLogStatus), default=TimeLogStatus.ACTIVE, nullable=False)
    
    # Notes
    notes = Column(Text, nullable=True)
      
    # System Information
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", backref="time_logs")
    
    # Database indexes for performance optimization
    __table_args__ = (
        Index('idx_time_log_user_id', 'user_id'),
        Index('idx_time_log_date', 'log_date'),
        Index('idx_time_log_status', 'status'),
        Index('idx_time_log_user_date', 'user_id', 'log_date'),
        Index('idx_time_log_created_at', 'created_at'),
        Index('idx_time_log_user_created', 'user_id', 'created_at'),
    )
class LogType(str, enum.Enum):
    ERROR = "error"
    SUCCESS = "success"

class Log(Base):
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, index=True)
    log_type = Column(Enum(LogType), nullable=False)
    message = Column(Text, nullable=False)
    module = Column(String, nullable=True)  # Module/route where log was created
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # User who triggered the action
    error_details = Column(Text, nullable=True)  # Stack trace or detailed error info
    request_path = Column(String, nullable=True)  # API endpoint path
    request_method = Column(String, nullable=True)  # HTTP method
    ip_address = Column(String, nullable=True)  # Client IP address
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", backref="logs")
    
    # Database indexes for performance optimization
    __table_args__ = (
        Index('idx_log_type', 'log_type'),
        Index('idx_log_created_at', 'created_at'),
        Index('idx_log_user_id', 'user_id'),
        Index('idx_log_module', 'module'),
        Index('idx_log_type_created', 'log_type', 'created_at'),
    )
