# HRMS Backend API Documentation

Comprehensive Human Resource Management System backend API built with FastAPI, PostgreSQL, and async SQLAlchemy.

## 📋 Table of Contents

- [Overview](#overview)
- [Base URL & Documentation](#base-url--documentation)
- [Authentication](#authentication)
- [API Endpoints](#api-endpoints)
  - [Authentication](#authentication-endpoints)
  - [Users](#users-endpoints)
  - [Leaves](#leaves-endpoints)
  - [Holidays](#holidays-endpoints)
  - [Tasks](#tasks-endpoints)
  - [Employees](#employees-endpoints)
  - [Admin](#admin-endpoints)
  - [Email Management](#email-management-endpoints)
- [Data Models](#data-models)
- [Error Handling](#error-handling)
- [Migration Guide](#migration-guide)

---

## Overview

**Version:** 1.0.0  
**Framework:** FastAPI 0.104.1  
**Database:** PostgreSQL with asyncpg  
**ORM:** SQLAlchemy 2.0 (async)

### Features
- ✅ User authentication with JWT
- ✅ Role-based access control (User, Admin, Super Admin)
- ✅ Leave management with half-day support
- ✅ Holiday tracking
- ✅ Task management
- ✅ Employee details & employment history
- ✅ Document uploads (Profile, Aadhaar, PAN)
- ✅ Email notifications
- ✅ Admin dashboard
- ✅ Database migrations (Alembic)

---

## Base URL & Documentation

```
http://localhost:8000
```

### Interactive Documentation
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## Authentication

The API uses **JWT (JSON Web Token)** for authentication.

### How to Authenticate

Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

### User Roles

- **USER**: Regular employee
- **ADMIN**: Administrative user with management permissions
- **SUPER_ADMIN**: Super administrator with full system access

---

## API Endpoints

### Authentication Endpoints

#### Register User
**POST** `/auth/register`

Register a new user with default USER role.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "name": "John Doe",
  "phone": "+1234567890",
  "designation": "Software Developer",
  "joining_date": "2024-01-15"
}
```

**Response:** 200 OK
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "John Doe",
  "phone": "+1234567890",
  "designation": "Software Developer",
  "joining_date": "2024-01-15",
  "role": "user",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

#### Login
**POST** `/auth/login`

Authenticate user and receive JWT token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:** 200 OK
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "role": "user"
  }
}
```

---

#### Get Current User
**GET** `/auth/me`

**Headers:** `Authorization: Bearer <token>`

**Response:** 200 OK - UserResponse object

---

#### Get Profile
**GET** `/auth/profile`

**Headers:** `Authorization: Bearer <token>`

**Response:** 200 OK - UserResponse object

---

#### Update Profile
**PUT** `/auth/profile`

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "name": "John Smith",
  "phone": "+1234567891",
  "designation": "Senior Developer",
  "joining_date": "2024-01-15"
}
```

**Response:** 200 OK - Updated UserResponse

---

#### Register Admin (Super Admin Only)
**POST** `/auth/register-admin`

**Headers:** `Authorization: Bearer <super_admin_token>`

**Request Body:**
```json
{
  "email": "admin@example.com",
  "password": "adminpass123",
  "name": "Admin User",
  "phone": "+1234567892",
  "designation": "HR Manager",
  "joining_date": "2024-01-01"
}
```

**Response:** 200 OK - UserResponse with role="admin"

---

### Users Endpoints

#### Get My Profile
**GET** `/users/profile`

**Headers:** `Authorization: Bearer <token>`

**Response:** 200 OK - UserResponse

---

#### Update My Profile
**PUT** `/users/profile`

**Headers:** `Authorization: Bearer <token>`

**Request Body:** (Same as PUT /auth/profile)

---

#### List All Users (Admin Only)
**GET** `/users?offset=0&limit=10`

**Headers:** `Authorization: Bearer <admin_token>`

**Query Parameters:**
- `offset` (int, default: 0)
- `limit` (int, default: 10)

**Response:** 200 OK - List[UserResponse]

---

#### Get User by ID (Admin Only)
**GET** `/users/{user_id}`

**Headers:** `Authorization: Bearer <admin_token>`

**Response:** 200 OK - UserResponse

---

#### Upload Profile Image
**POST** `/users/upload-profile-image`

**Content-Type:** `multipart/form-data`

**Headers:** `Authorization: Bearer <token>`

**Body:** File upload (JPG, PNG, PDF, max 10MB)

**Response:** 200 OK
```json
{
  "filename": "photo.jpg",
  "file_path": "uploads/1_profile_uuid.jpg",
  "file_size": 123456,
  "content_type": "image/jpeg"
}
```

**Note:** Profile images are auto-approved.

---

#### Upload Aadhaar Front
**POST** `/users/upload-aadhaar-front`

**Content-Type:** `multipart/form-data`

**Headers:** `Authorization: Bearer <token>`

**Status:** Pending (requires admin approval)

---

#### Upload Aadhaar Back
**POST** `/users/upload-aadhaar-back`

**Content-Type:** `multipart/form-data`

**Headers:** `Authorization: Bearer <token>`

**Status:** Pending

---

#### Upload PAN
**POST** `/users/upload-pan`

**Content-Type:** `multipart/form-data`

**Headers:** `Authorization: Bearer <token>`

**Status:** Pending

---

#### Get My Employee Details
**GET** `/users/my-employee-details`

**Headers:** `Authorization: Bearer <token>`

**Response:** 200 OK - EmployeeDetailsResponse or null

---

#### Get My Employment History
**GET** `/users/my-employment-history`

**Headers:** `Authorization: Bearer <token>`

**Response:** 200 OK - List[EmploymentHistoryResponse]

---

#### Get My Employee Summary
**GET** `/users/my-employee-summary`

**Headers:** `Authorization: Bearer <token>`

**Response:** 200 OK - EmployeeSummary

---

#### Get Department Colleagues
**GET** `/users/my-department-colleagues`

**Headers:** `Authorization: Bearer <token>`

**Response:** 200 OK
```json
{
  "department": "Engineering",
  "colleagues": [
    {
      "id": 2,
      "name": "Jane Smith",
      "email": "jane@example.com",
      "designation": "Senior Developer"
    }
  ]
}
```

---

#### Get My Manager
**GET** `/users/my-manager`

**Headers:** `Authorization: Bearer <token>`

**Response:** 200 OK
```json
{
  "manager": {
    "id": 5,
    "name": "Manager Name",
    "email": "manager@example.com",
    "designation": "Engineering Manager",
    "phone": "+1234567890"
  }
}
```

---

### Leaves Endpoints

#### Apply for Leave
**POST** `/leaves`

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "start_date": "2024-02-01T00:00:00Z",
  "end_date": "2024-02-03T00:00:00Z",
  "total_days": 3.0,
  "reason": "Family vacation"
}
```

**Response:** 200 OK
```json
{
  "id": 1,
  "user_id": 1,
  "start_date": "2024-02-01T00:00:00Z",
  "end_date": "2024-02-03T00:00:00Z",
  "total_days": 3.0,
  "reason": "Family vacation",
  "status": "pending",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Notes:**
- Supports half-days (0.5 increments): 1.0, 1.5, 2.0, 2.5
- Dates must be timezone-aware
- Cannot apply for past dates
- Overlapping leaves prevented

---

#### Get My Leaves
**GET** `/leaves/my-leaves?offset=0&limit=10`

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `offset` (int, default: 0)
- `limit` (int, default: 10)

**Response:** 200 OK - List[LeaveResponse]

---

#### Get All Leaves (Admin Only)
**GET** `/leaves?offset=0&limit=10`

**Headers:** `Authorization: Bearer <admin_token>`

**Response:** 200 OK - List[LeaveResponse with user info]

---

#### Update Leave
**PUT** `/leaves/{leave_id}`

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "start_date": "2024-02-02T00:00:00Z",
  "end_date": "2024-02-04T00:00:00Z",
  "total_days": 2.5,
  "reason": "Updated reason",
  "status": "approved"
}
```

**Notes:**
- Users can only edit pending leaves
- Admins can edit any leave
- Only admins can change status

**Response:** 200 OK - LeaveResponse

---

#### Update Leave Status (Admin Only)
**PUT** `/leaves/{leave_id}/status`

**Headers:** `Authorization: Bearer <admin_token>`

**Request Body:**
```json
{
  "status": "approved"
}
```

**Status values:** `pending`, `approved`, `rejected`

**Response:** 200 OK - LeaveResponse

---

#### Get Leave by ID
**GET** `/leaves/{leave_id}`

**Headers:** `Authorization: Bearer <token>`

**Response:** 200 OK - LeaveResponse

---

### Holidays Endpoints

#### Create Holiday (Admin Only)
**POST** `/holidays`

**Headers:** `Authorization: Bearer <admin_token>`

**Request Body:**
```json
{
  "date": "2024-12-25T00:00:00Z",
  "title": "Christmas Day",
  "description": "Official holiday",
  "is_active": true
}
```

**Response:** 200 OK - HolidayResponse

---

#### Get All Holidays
**GET** `/holidays?offset=0&limit=10`

**Headers:** `Authorization: Bearer <token>`

**Response:** 200 OK - List[HolidayResponse]

---

#### Get Upcoming Holidays
**GET** `/holidays/upcoming`

**Headers:** `Authorization: Bearer <token>`

**Response:** 200 OK - List[HolidayResponse]

---

#### Get Holiday by ID
**GET** `/holidays/{holiday_id}`

**Headers:** `Authorization: Bearer <token>`

**Response:** 200 OK - HolidayResponse

---

#### Update Holiday (Admin Only)
**PUT** `/holidays/{holiday_id}`

**Headers:** `Authorization: Bearer <admin_token>`

**Request Body:**
```json
{
  "title": "Christmas Day - Updated",
  "description": "Updated description",
  "is_active": false
}
```

**Response:** 200 OK - HolidayResponse

---

#### Delete Holiday (Admin Only)
**DELETE** `/holidays/{holiday_id}`

**Headers:** `Authorization: Bearer <admin_token>`

**Response:** 200 OK
```json
{
  "message": "Holiday deleted successfully"
}
```

---

### Tasks Endpoints

#### Create Task
**POST** `/tasks`

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "name": "Complete project documentation",
  "description": "Write comprehensive API docs",
  "due_date": "2024-02-15T00:00:00Z",
  "priority": "high",
  "category": "work"
}
```

**Priority values:** `low`, `medium`, `high`, `urgent`

**Response:** 200 OK - TaskResponse

---

#### Get My Tasks
**GET** `/tasks/my-tasks?status=pending&priority=high&category=work&overdue_only=false`

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `status` (optional): `pending`, `in_progress`, `completed`, `cancelled`
- `priority` (optional): `low`, `medium`, `high`, `urgent`
- `category` (optional): Filter by category
- `overdue_only` (bool, default: false): Show only overdue tasks

**Response:** 200 OK - List[TaskResponse]

---

#### Update Task
**PUT** `/tasks/{task_id}`

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "name": "Updated task name",
  "status": "in_progress",
  "priority": "urgent",
  "due_date": "2024-03-15T00:00:00Z"
}
```

**Response:** 200 OK - TaskResponse

---

#### Delete Task
**DELETE** `/tasks/{task_id}`

**Headers:** `Authorization: Bearer <token>`

**Response:** 200 OK - Soft delete (sets is_active=false)

---

#### Get Task Summary
**GET** `/tasks/summary`

**Headers:** `Authorization: Bearer <token>`

**Response:** 200 OK
```json
{
  "total_tasks": 25,
  "pending_tasks": 10,
  "in_progress_tasks": 5,
  "completed_tasks": 8,
  "cancelled_tasks": 2,
  "overdue_tasks": 3
}
```

---

### Employees Endpoints

#### Create Employee Details (Admin Only)
**POST** `/employees/details`

**Headers:** `Authorization: Bearer <admin_token>`

**Request Body:**
```json
{
  "user_id": 1,
  "employee_id": "EMP001",
  "department": "Engineering",
  "employment_type": "Full-time",
  "work_location": "Mumbai Office",
  "basic_salary": "50000",
  "currency": "INR",
  "manager_id": 5
}
```

**Response:** 200 OK - EmployeeDetailsResponse

---

#### Get Employee Details (Admin Only)
**GET** `/employees/details/{user_id}`

**Headers:** `Authorization: Bearer <admin_token>`

**Response:** 200 OK - EmployeeDetailsResponse

---

#### Update Employee Details (Admin Only)
**PUT** `/employees/details/{user_id}`

**Headers:** `Authorization: Bearer <admin_token>`

**Request Body:** All fields optional

**Response:** 200 OK - EmployeeDetailsResponse

---

#### Create Employment History (Admin Only)
**POST** `/employees/employment-history`

**Headers:** `Authorization: Bearer <admin_token>`

**Request Body:**
```json
{
  "user_id": 1,
  "position_title": "Senior Developer",
  "department": "Engineering",
  "start_date": "2024-01-15",
  "salary": "60000",
  "currency": "INR",
  "is_current": true
}
```

**Response:** 200 OK - EmploymentHistoryResponse

---

#### Get Employment History (Admin Only)
**GET** `/employees/employment-history/{user_id}`

**Headers:** `Authorization: Bearer <admin_token>`

**Response:** 200 OK - List[EmploymentHistoryResponse]

---

### Admin Endpoints

#### Get Dashboard Statistics
**GET** `/admin/dashboard`

**Headers:** `Authorization: Bearer <admin_token>`

**Response:** 200 OK
```json
{
  "total_users": 50,
  "active_users": 45,
  "pending_leaves": 12,
  "upcoming_holidays": 3
}
```

---

#### Create User (Admin Only)
**POST** `/admin/users`

**Headers:** `Authorization: Bearer <admin_token>`

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "password": "password123",
  "name": "New User",
  "phone": "+1234567890",
  "designation": "Junior Developer",
  "joining_date": "2024-01-20"
}
```

**Response:** 200 OK - UserResponse

---

#### Update User (Admin Only)
**PUT** `/admin/users/{user_id}`

**Headers:** `Authorization: Bearer <admin_token>`

**Request Body:** AdminUserUpdate (all fields optional)

**Response:** 200 OK - UserResponse

---

#### Activate User
**PUT** `/admin/users/{user_id}/activate`

**Headers:** `Authorization: Bearer <admin_token>`

**Response:** 200 OK

---

#### Deactivate User
**PUT** `/admin/users/{user_id}/deactivate`

**Headers:** `Authorization: Bearer <admin_token>`

**Response:** 200 OK

---

#### Delete User
**DELETE** `/admin/users/{user_id}`

**Headers:** `Authorization: Bearer <admin_token>`

**Response:** 200 OK

**Note:** Cannot delete super admin or your own account

---

#### Upload Document for User (Super Admin Only)
**POST** `/admin/users/{user_id}/upload-profile-image`
**POST** `/admin/users/{user_id}/upload-aadhaar-front`
**POST** `/admin/users/{user_id}/upload-aadhaar-back`
**POST** `/admin/users/{user_id}/upload-pan`

**Content-Type:** `multipart/form-data`

**Headers:** `Authorization: Bearer <super_admin_token>`

**Response:** 200 OK - FileUploadResponse

---

### Email Management Endpoints

#### Get Email Settings (Super Admin Only)
**GET** `/email/settings`

**Headers:** `Authorization: Bearer <super_admin_token>`

**Response:** 200 OK - EmailSettingsResponse

---

#### Create Email Settings (Super Admin Only)
**POST** `/email/settings`

**Headers:** `Authorization: Bearer <super_admin_token>`

**Request Body:**
```json
{
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "smtp_username": "your-email@gmail.com",
  "smtp_password": "your-password",
  "smtp_use_tls": true,
  "smtp_use_ssl": false,
  "from_email": "your-email@gmail.com",
  "from_name": "HRMS System"
}
```

**Response:** 200 OK - EmailSettingsResponse

---

#### Update Email Settings (Super Admin Only)
**PUT** `/email/settings/{settings_id}`

**Headers:** `Authorization: Bearer <super_admin_token>`

**Request Body:** EmailSettingsUpdate (all fields optional)

**Response:** 200 OK - EmailSettingsResponse

---

#### Test Email Connection (Super Admin Only)
**POST** `/email/settings/test-connection`

**Headers:** `Authorization: Bearer <super_admin_token>`

**Response:** 200 OK
```json
{
  "success": true,
  "message": "Connection test successful"
}
```

---

#### Get Email Templates (Super Admin Only)
**GET** `/email/templates`

**Headers:** `Authorization: Bearer <super_admin_token>`

**Response:** 200 OK - List[EmailTemplateResponse]

---

#### Create Email Template (Super Admin Only)
**POST** `/email/templates`

**Headers:** `Authorization: Bearer <super_admin_token>`

**Request Body:**
```json
{
  "name": "welcome_email",
  "subject": "Welcome to HRMS",
  "body": "Welcome {{name}}!",
  "template_type": "welcome",
  "is_active": true
}
```

**Response:** 200 OK - EmailTemplateResponse

---

#### Update Email Template (Super Admin Only)
**PUT** `/email/templates/{template_id}`

**Headers:** `Authorization: Bearer <super_admin_token>`

**Request Body:** EmailTemplateUpdate

**Response:** 200 OK - EmailTemplateResponse

---

#### Delete Email Template (Super Admin Only)
**DELETE** `/email/templates/{template_id}`

**Headers:** `Authorization: Bearer <super_admin_token>`

**Response:** 200 OK
```json
{
  "message": "Template deleted successfully"
}
```

---

#### Send Email (Super Admin Only)
**POST** `/email/send`

**Headers:** `Authorization: Bearer <super_admin_token>`

**Request Body:**
```json
{
  "recipient_email": "user@example.com",
  "recipient_name": "John Doe",
  "subject": "Welcome",
  "body": "Welcome to HRMS!",
  "template_type": "welcome"
}
```

**Response:** 200 OK
```json
{
  "success": true,
  "message": "Email sent successfully"
}
```

---

#### Send Bulk Emails (Super Admin Only)
**POST** `/email/send-bulk`

**Headers:** `Authorization: Bearer <super_admin_token>`

**Request Body:**
```json
{
  "recipient_emails": ["user1@example.com", "user2@example.com"],
  "recipient_names": ["User 1", "User 2"],
  "subject": "Announcement",
  "body": "Important announcement",
  "template_type": "announcement"
}
```

**Response:** 200 OK - Bulk send results

---

#### Get Email Logs (Super Admin Only)
**GET** `/email/logs?offset=0&limit=10&status_filter=sent`

**Headers:** `Authorization: Bearer <super_admin_token>`

**Query Parameters:**
- `offset` (int, default: 0)
- `limit` (int, default: 10, max: 100)
- `status_filter` (optional): Filter by status

**Response:** 200 OK - PaginatedResponse

---

#### Get Users for Email (Super Admin Only)
**GET** `/email/users`

**Headers:** `Authorization: Bearer <super_admin_token>`

**Response:** 200 OK - List of active users with email and designation

---

## Data Models

### UserResponse
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "John Doe",
  "phone": "+1234567890",
  "designation": "Software Developer",
  "joining_date": "2024-01-15",
  "role": "user",
  "is_active": true,
  "profile_image": "uploads/1_profile_uuid.jpg",
  "profile_image_status": "approved",
  "aadhaar_front": "uploads/1_aadhaar_front_uuid.jpg",
  "aadhaar_front_status": "pending",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": null
}
```

### LeaveResponse
```json
{
  "id": 1,
  "user_id": 1,
  "start_date": "2024-02-01T00:00:00Z",
  "end_date": "2024-02-03T00:00:00Z",
  "total_days": 3.0,
  "reason": "Family vacation",
  "status": "pending",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### HolidayResponse
```json
{
  "id": 1,
  "date": "2024-12-25T00:00:00Z",
  "title": "Christmas Day",
  "description": "Official holiday",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### TaskResponse
```json
{
  "id": 1,
  "user_id": 1,
  "name": "Complete documentation",
  "description": "Write API docs",
  "status": "pending",
  "due_date": "2024-02-15T00:00:00Z",
  "priority": "high",
  "category": "work",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Validation Error |
| 500 | Internal Server Error |

### Error Response Format
```json
{
  "detail": "Error message description"
}
```

---

## Migration Guide

### Running Migrations

#### Using Alembic (Recommended)
```bash
# Create migration
python run_alembic_migration.py revision --autogenerate -m "Description"

# Apply migrations
python run_alembic_migration.py upgrade head

# Check current version
python run_alembic_migration.py current
```

#### Using Legacy Script
```bash
python run_migration.py
```

**For detailed migration documentation, see:**
- `ALEMBIC_SETUP.md` - Alembic guide
- `MIGRATIONS_README.md` - Quick start
- `MIGRATION_QUICK_REFERENCE.md` - Command reference

---

## Important Notes

### Date/Time Format
- All datetimes must be timezone-aware (ISO 8601 with timezone)
- Example: `2024-01-15T10:30:00Z`
- Supports multiple date formats (YYYY-MM-DD, MM/DD/YYYY, etc.)

### File Uploads
- Maximum size: 10MB
- Allowed formats: JPG, JPEG, PNG, PDF
- Profile images: Auto-approved
- Documents (Aadhaar, PAN): Require admin approval

### Pagination
- Default: `offset=0`, `limit=10`
- Maximum limit typically: 100

### Permissions
- **User**: Own data only
- **Admin**: All user data + management
- **Super Admin**: Full system access

### Leave Total Days
- Supports half-days with 0.5 increments
- Examples: 1.0, 1.5, 2.0, 2.5
- Cannot exceed actual date range

---

## Health Check

**GET** `/health`

**Response:** 200 OK
```json
{
  "status": "healthy",
  "message": "HRMS Backend is running"
}
```

---

## API Information

**GET** `/`

**Response:** 200 OK
```json
{
  "message": "HRMS Backend API",
  "version": "1.0.0",
  "docs": "/docs",
  "redoc": "/redoc"
}
```

---

**For the most up-to-date API documentation, visit:**
- Interactive Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
