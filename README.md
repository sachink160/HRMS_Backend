# HRMS (Human Resource Management System) API Documentation

A comprehensive REST API for managing human resources, employee attendance, leave management, and holiday tracking.

## Table of Contents

- [Base URL](#base-url)
- [Authentication](#authentication)
- [API Endpoints](#api-endpoints)
  - [Authentication Endpoints](#authentication-endpoints)
  - [User Management Endpoints](#user-management-endpoints)
  - [Leave Management Endpoints](#leave-management-endpoints)
  - [Time Tracking Endpoints](#time-tracking-endpoints)
  - [Holiday Management Endpoints](#holiday-management-endpoints)
  - [Admin Management Endpoints](#admin-management-endpoints)
- [Data Models](#data-models)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)

## Base URL

```
http://localhost:8000
```

## Authentication

The API uses JWT (JSON Web Token) for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

### User Roles

- **USER**: Regular employee with basic permissions
- **ADMIN**: Administrative user with management permissions
- **SUPER_ADMIN**: Super administrator with full system access

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

**Response:**
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
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": null
}
```

#### Login User
**POST** `/auth/login`

Authenticate user and receive access token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "phone": "+1234567890",
    "role": "user",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": null
  }
}
```

#### Get Current User Profile
**GET** `/auth/me`

Get current authenticated user information.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
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
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": null
}
```

#### Update Profile
**PUT** `/auth/profile`

Update current user's profile information.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "name": "John Smith",
  "phone": "+1234567891",
  "designation": "Senior Software Developer",
  "joining_date": "2024-01-15"
}
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "John Smith",
  "phone": "+1234567891",
  "designation": "Senior Software Developer",
  "joining_date": "2024-01-15",
  "role": "user",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

#### Register Admin (Super Admin Only)
**POST** `/auth/register-admin`

Register a new admin user (requires super admin privileges).

**Headers:**
```
Authorization: Bearer <super_admin_token>
```

**Request Body:**
```json
{
  "email": "admin@example.com",
  "password": "adminpassword123",
  "name": "Admin User",
  "phone": "+1234567892",
  "designation": "HR Manager",
  "joining_date": "2024-01-01"
}
```

**Response:**
```json
{
  "id": 2,
  "email": "admin@example.com",
  "name": "Admin User",
  "phone": "+1234567892",
  "designation": "HR Manager",
  "joining_date": "2024-01-01",
  "role": "admin",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": null
}
```

### User Management Endpoints

#### Get User Profile
**GET** `/users/profile`

Get current user's profile (same as `/auth/me`).

**Headers:**
```
Authorization: Bearer <token>
```

#### Update User Profile
**PUT** `/users/profile`

Update current user's profile (same as `/auth/profile`).

**Headers:**
```
Authorization: Bearer <token>
```

#### List All Users (Admin Only)
**GET** `/users?offset=0&limit=10`

Get paginated list of all users.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Query Parameters:**
- `offset` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records to return (default: 10)

**Response:**
```json
[
  {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "phone": "+1234567890",
    "designation": "Software Developer",
    "joining_date": "2024-01-15",
    "role": "user",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": null
  }
]
```

#### Get User by ID (Admin Only)
**GET** `/users/{user_id}`

Get specific user by ID.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Response:**
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
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": null
}
```

### Leave Management Endpoints

#### Apply for Leave
**POST** `/leaves`

Submit a new leave application.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "start_date": "2024-02-01T00:00:00Z",
  "end_date": "2024-02-03T00:00:00Z",
  "reason": "Family vacation"
}
```

**Response:**
```json
{
  "id": 1,
  "user_id": 1,
  "start_date": "2024-02-01T00:00:00Z",
  "end_date": "2024-02-03T00:00:00Z",
  "reason": "Family vacation",
  "status": "pending",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": null
}
```

#### Get My Leaves
**GET** `/leaves/my-leaves?offset=0&limit=10`

Get current user's leave applications.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `offset` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records to return (default: 10)

**Response:**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "start_date": "2024-02-01T00:00:00Z",
    "end_date": "2024-02-03T00:00:00Z",
    "reason": "Family vacation",
    "status": "pending",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": null
  }
]
```

#### Get All Leaves (Admin Only)
**GET** `/leaves?offset=0&limit=10`

Get all leave applications with user information.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Response:**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "start_date": "2024-02-01T00:00:00Z",
    "end_date": "2024-02-03T00:00:00Z",
    "reason": "Family vacation",
    "status": "pending",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": null,
    "user": {
      "id": 1,
      "email": "user@example.com",
      "name": "John Doe",
      "phone": "+1234567890",
      "designation": "Software Developer",
      "joining_date": "2024-01-15",
      "role": "user",
      "is_active": true,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": null
    }
  }
]
```

#### Update Leave Status (Admin Only)
**PUT** `/leaves/{leave_id}/status`

Update leave application status (approve/reject).

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Request Body:**
```json
{
  "status": "approved"
}
```

**Response:**
```json
{
  "id": 1,
  "user_id": 1,
  "start_date": "2024-02-01T00:00:00Z",
  "end_date": "2024-02-03T00:00:00Z",
  "reason": "Family vacation",
  "status": "approved",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

#### Get Leave by ID
**GET** `/leaves/{leave_id}`

Get specific leave application by ID.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": 1,
  "user_id": 1,
  "start_date": "2024-02-01T00:00:00Z",
  "end_date": "2024-02-03T00:00:00Z",
  "reason": "Family vacation",
  "status": "approved",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:00:00Z",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "phone": "+1234567890",
    "designation": "Software Developer",
    "joining_date": "2024-01-15",
    "role": "user",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": null
  }
}
```

### Time Tracking Endpoints

#### Check In
**POST** `/trackers/check-in`

Record check-in time for the current day.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": 1,
  "user_id": 1,
  "check_in": "2024-01-15T09:00:00Z",
  "check_out": null,
  "date": "2024-01-15T00:00:00Z",
  "created_at": "2024-01-15T09:00:00Z",
  "updated_at": "2024-01-15T09:00:00Z"
}
```

#### Check Out
**POST** `/trackers/check-out`

Record check-out time for the current day.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": 1,
  "user_id": 1,
  "check_in": "2024-01-15T09:00:00Z",
  "check_out": "2024-01-15T17:00:00Z",
  "date": "2024-01-15T00:00:00Z",
  "created_at": "2024-01-15T09:00:00Z",
  "updated_at": "2024-01-15T17:00:00Z"
}
```

#### Get My Tracking Records
**GET** `/trackers/my-tracking?offset=0&limit=10`

Get current user's time tracking records.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `offset` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records to return (default: 10)

**Response:**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "check_in": "2024-01-15T09:00:00Z",
    "check_out": "2024-01-15T17:00:00Z",
    "date": "2024-01-15T00:00:00Z",
    "created_at": "2024-01-15T09:00:00Z",
    "updated_at": "2024-01-15T17:00:00Z"
  }
]
```

#### Get Today's Tracking
**GET** `/trackers/today`

Get today's tracking record for current user.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": 1,
  "user_id": 1,
  "check_in": "2024-01-15T09:00:00Z",
  "check_out": null,
  "date": "2024-01-15T00:00:00Z",
  "created_at": "2024-01-15T09:00:00Z",
  "updated_at": "2024-01-15T09:00:00Z"
}
```

#### Get Today's Status
**GET** `/trackers/today-status`

Get today's status with calculated total hours.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "check_in_time": "2024-01-15T09:00:00Z",
  "check_out_time": "2024-01-15T17:00:00Z",
  "total_hours": 8.0
}
```

#### Get My Attendance
**GET** `/trackers/my-attendance?offset=0&limit=30`

Get current user's attendance history with calculated hours.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "check_in": "2024-01-15T09:00:00Z",
    "check_out": "2024-01-15T17:00:00Z",
    "date": "2024-01-15T00:00:00Z",
    "created_at": "2024-01-15T09:00:00Z",
    "updated_at": "2024-01-15T17:00:00Z",
    "total_hours": 8.0
  }
]
```

#### Get All Tracking Records (Admin Only)
**GET** `/trackers?offset=0&limit=10`

Get all tracking records with user information.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Response:**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "check_in": "2024-01-15T09:00:00Z",
    "check_out": "2024-01-15T17:00:00Z",
    "date": "2024-01-15T00:00:00Z",
    "created_at": "2024-01-15T09:00:00Z",
    "updated_at": "2024-01-15T17:00:00Z",
    "user": {
      "id": 1,
      "email": "user@example.com",
      "name": "John Doe",
      "phone": "+1234567890",
      "designation": "Software Developer",
      "joining_date": "2024-01-15",
      "role": "user",
      "is_active": true,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": null
    }
  }
]
```

#### Get User Tracking (Admin Only)
**GET** `/trackers/user/{user_id}?offset=0&limit=10`

Get tracking records for specific user.

**Headers:**
```
Authorization: Bearer <admin_token>
```

### Holiday Management Endpoints

#### Create Holiday (Admin Only)
**POST** `/holidays`

Create a new holiday.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Request Body:**
```json
{
  "date": "2024-12-25",
  "title": "Christmas Day",
  "description": "Official holiday"
}
```

**Note:** Date should be in `YYYY-MM-DD` format (date string) or `YYYY-MM-DDTHH:MM:SS` format (datetime string).

**Response:**
```json
{
  "id": 1,
  "date": "2024-12-25T00:00:00Z",
  "title": "Christmas Day",
  "description": "Official holiday",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": null
}
```

#### Get All Holidays
**GET** `/holidays?offset=0&limit=10`

Get paginated list of all holidays.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "id": 1,
    "date": "2024-12-25T00:00:00Z",
    "title": "Christmas Day",
    "description": "Official holiday",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": null
  }
]
```

#### Get Upcoming Holidays
**GET** `/holidays/upcoming`

Get all upcoming holidays.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "id": 1,
    "date": "2024-12-25T00:00:00Z",
    "title": "Christmas Day",
    "description": "Official holiday",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": null
  }
]
```

#### Get Holiday by ID
**GET** `/holidays/{holiday_id}`

Get specific holiday by ID.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": 1,
  "date": "2024-12-25T00:00:00Z",
  "title": "Christmas Day",
  "description": "Official holiday",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": null
}
```

#### Update Holiday (Admin Only)
**PUT** `/holidays/{holiday_id}`

Update holiday information.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Request Body:**
```json
{
  "date": "2024-12-25",
  "title": "Christmas Day - Updated",
  "description": "Official holiday - Updated description"
}
```

**Note:** All fields are optional. Date should be in `YYYY-MM-DD` format if provided.

**Response:**
```json
{
  "id": 1,
  "date": "2024-12-25T00:00:00Z",
  "title": "Christmas Day - Updated",
  "description": "Official holiday - Updated description",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

#### Delete Holiday (Admin Only)
**DELETE** `/holidays/{holiday_id}`

Delete a holiday.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "message": "Holiday deleted successfully"
}
```

### Admin Management Endpoints

#### Get Dashboard Statistics (Admin Only)
**GET** `/admin/dashboard`

Get dashboard statistics including total users, active users, pending leaves, and upcoming holidays.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "total_users": 50,
  "active_users_today": 45,
  "pending_leaves": 12,
  "upcoming_holidays": 3
}
```

#### Create User (Admin Only)
**POST** `/admin/users?role=user`

Create a new user with specified role.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Query Parameters:**
- `role` (optional): User role - "user" or "admin" (default: "user")

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "password": "password123",
  "name": "New User",
  "phone": "+1234567893",
  "designation": "Junior Developer",
  "joining_date": "2024-01-20"
}
```

**Response:**
```json
{
  "id": 3,
  "email": "newuser@example.com",
  "name": "New User",
  "phone": "+1234567893",
  "designation": "Junior Developer",
  "joining_date": "2024-01-20",
  "role": "user",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": null
}
```

#### Update User (Admin Only)
**PUT** `/admin/users/{user_id}`

Update user information.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Request Body:**
```json
{
  "name": "Updated Name",
  "email": "updated@example.com",
  "phone": "+1234567894",
  "designation": "Senior Developer",
  "role": "admin"
}
```

**Response:**
```json
{
  "id": 3,
  "email": "updated@example.com",
  "name": "Updated Name",
  "phone": "+1234567894",
  "designation": "Senior Developer",
  "joining_date": "2024-01-20",
  "role": "admin",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

#### Get All Users (Admin Only)
**GET** `/admin/users?offset=0&limit=10`

Get paginated list of all users.

**Headers:**
```
Authorization: Bearer <admin_token>
```

#### Get All Leaves (Admin Only)
**GET** `/admin/leaves?offset=0&limit=10&status_filter=pending`

Get all leave applications with optional status filter.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Query Parameters:**
- `offset` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records to return (default: 10)
- `status_filter` (optional): Filter by status - "pending", "approved", "rejected"

#### Get All Tracking Records (Admin Only)
**GET** `/admin/tracking?offset=0&limit=10&date_filter=2024-01-15`

Get all tracking records with optional date filter.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Query Parameters:**
- `offset` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records to return (default: 10)
- `date_filter` (optional): Filter by specific date (YYYY-MM-DD format)

#### Get User Summary (Admin Only)
**GET** `/admin/user/{user_id}/summary`

Get comprehensive summary for a specific user including leaves and tracking records.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "phone": "+1234567890",
    "designation": "Software Developer",
    "joining_date": "2024-01-15",
    "role": "user",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": null
  },
  "leaves": {
    "total": 5,
    "approved": 3,
    "pending": 1,
    "rejected": 1,
    "recent": [...]
  },
  "tracking": {
    "recent_records": [...],
    "total_records": 30
  }
}
```

#### Approve Leave (Admin Only)
**PUT** `/admin/leaves/{leave_id}/approve`

Approve a leave application.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "message": "Leave approved successfully",
  "leave": {
    "id": 1,
    "user_id": 1,
    "start_date": "2024-02-01T00:00:00Z",
    "end_date": "2024-02-03T00:00:00Z",
    "reason": "Family vacation",
    "status": "approved",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T11:00:00Z"
  }
}
```

#### Reject Leave (Admin Only)
**PUT** `/admin/leaves/{leave_id}/reject`

Reject a leave application.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "message": "Leave rejected successfully",
  "leave": {
    "id": 1,
    "user_id": 1,
    "start_date": "2024-02-01T00:00:00Z",
    "end_date": "2024-02-03T00:00:00Z",
    "reason": "Family vacation",
    "status": "rejected",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T11:00:00Z"
  }
}
```

#### Get Pending Leaves (Admin Only)
**GET** `/admin/leaves/pending?offset=0&limit=10`

Get all pending leave applications.

**Headers:**
```
Authorization: Bearer <admin_token>
```

#### Create Bulk Holidays (Admin Only)
**POST** `/admin/holidays/bulk`

Create multiple holidays at once.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Request Body:**
```json
[
  {
    "date": "2024-12-25T00:00:00Z",
    "title": "Christmas Day",
    "description": "Official holiday"
  },
  {
    "date": "2024-01-01T00:00:00Z",
    "title": "New Year's Day",
    "description": "Official holiday"
  }
]
```

**Response:**
```json
[
  {
    "id": 1,
    "date": "2024-12-25T00:00:00Z",
    "title": "Christmas Day",
    "description": "Official holiday",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": null
  },
  {
    "id": 2,
    "date": "2024-01-01T00:00:00Z",
    "title": "New Year's Day",
    "description": "Official holiday",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": null
  }
]
```

#### Get Attendance Report (Admin Only)
**GET** `/admin/reports/attendance?start_date=2024-01-01&end_date=2024-01-31`

Get attendance report for date range.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Query Parameters:**
- `start_date` (optional): Start date for report (YYYY-MM-DD format)
- `end_date` (optional): End date for report (YYYY-MM-DD format)

**Response:**
```json
{
  "period": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  },
  "attendance": [
    {
      "user": {
        "id": 1,
        "email": "user@example.com",
        "name": "John Doe"
      },
      "records": [...]
    }
  ]
}
```

#### Get All Holidays (Admin Only)
**GET** `/admin/holidays?offset=0&limit=10`

Get all holidays with admin privileges.

**Headers:**
```
Authorization: Bearer <admin_token>
```

#### Activate User (Admin Only)
**PUT** `/admin/users/{user_id}/activate`

Activate a user account.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "message": "User activated successfully",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "is_active": true
  }
}
```

#### Deactivate User (Admin Only)
**PUT** `/admin/users/{user_id}/deactivate`

Deactivate a user account.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "message": "User deactivated successfully",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "is_active": false
  }
}
```

#### Update User Role (Admin Only)
**PUT** `/admin/users/{user_id}/role?new_role=admin`

Update user role.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Query Parameters:**
- `new_role`: New role - "user" or "admin"

**Response:**
```json
{
  "message": "User role updated to admin",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "role": "admin"
  }
}
```

#### Toggle User Status (Admin Only)
**PUT** `/admin/users/{user_id}/toggle-status`

Toggle user active status.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "message": "User activated successfully",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "is_active": true
  }
}
```

#### Promote User (Admin Only)
**PUT** `/admin/users/{user_id}/promote`

Promote user to admin role.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "message": "User promoted to admin successfully",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "role": "admin"
  }
}
```

#### Delete User (Admin Only)
**DELETE** `/admin/users/{user_id}`

Delete a user account permanently. This will also delete all related records including:
- User tracking records (check-in/check-out history)
- Leave applications
- Any other user-related data

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "message": "User deleted successfully"
}
```

**Note:** 
- Cannot delete super admin users or your own account
- This action is irreversible and will permanently delete all user data

#### Get Leaves Report (Admin Only)
**GET** `/admin/reports/leaves?start_date=2024-01-01&end_date=2024-01-31&status_filter=pending`

Get comprehensive leaves report.

**Headers:**
```
Authorization: Bearer <admin_token>
```

**Query Parameters:**
- `start_date` (optional): Start date for report (YYYY-MM-DD format)
- `end_date` (optional): End date for report (YYYY-MM-DD format)
- `status_filter` (optional): Filter by status - "pending", "approved", "rejected"

**Response:**
```json
{
  "period": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  },
  "statistics": {
    "total": 25,
    "approved": 20,
    "pending": 3,
    "rejected": 2
  },
  "leaves": [...]
}
```

## Data Models

### User
```json
{
  "id": "integer",
  "email": "string (email)",
  "name": "string",
  "phone": "string (optional)",
  "designation": "string (optional)",
  "joining_date": "date (optional)",
  "role": "enum (user, admin, super_admin)",
  "is_active": "boolean",
  "created_at": "datetime",
  "updated_at": "datetime (optional)"
}
```

### Leave
```json
{
  "id": "integer",
  "user_id": "integer",
  "start_date": "datetime",
  "end_date": "datetime",
  "reason": "string",
  "status": "enum (pending, approved, rejected)",
  "created_at": "datetime",
  "updated_at": "datetime (optional)",
  "user": "User (optional)"
}
```

### Holiday
```json
{
  "id": "integer",
  "date": "datetime",
  "title": "string",
  "description": "string (optional)",
  "created_at": "datetime",
  "updated_at": "datetime (optional)"
}
```

### UserTracker
```json
{
  "id": "integer",
  "user_id": "integer",
  "check_in": "datetime (optional)",
  "check_out": "datetime (optional)",
  "date": "datetime",
  "created_at": "datetime",
  "updated_at": "datetime (optional)",
  "user": "User (optional)",
  "total_hours": "float (optional, calculated)"
}
```

## Error Handling

The API uses standard HTTP status codes:

- **200 OK**: Request successful
- **201 Created**: Resource created successfully
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **422 Unprocessable Entity**: Validation error
- **500 Internal Server Error**: Server error

### Error Response Format
```json
{
  "detail": "Error message description"
}
```

### Common Error Examples

#### 400 Bad Request
```json
{
  "detail": "Email already registered"
}
```

#### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

#### 403 Forbidden
```json
{
  "detail": "Not enough permissions"
}
```

#### 404 Not Found
```json
{
  "detail": "User not found"
}
```

## Rate Limiting

Currently, there are no rate limits implemented. However, it's recommended to implement rate limiting in production environments to prevent abuse.

## Notes

- All datetime fields are in ISO 8601 format with timezone information
- JWT tokens expire after 30 minutes by default
- Password requirements: Minimum 8 characters (recommended)
- All endpoints require authentication except for user registration
- Admin endpoints require admin or super_admin role
- Super admin endpoints require super_admin role only
- Pagination is available for list endpoints with default limit of 10 items
- All timestamps are in UTC timezone
