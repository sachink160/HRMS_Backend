# Admin Module

**File**: [`app/routes/admin.py`](file:///d:/SP/HRMS/Backend/app/routes/admin.py)  
**Authorization**: Admin role required for all endpoints

## Overview

The Admin module provides comprehensive administrative features for managing users, tracking, time corrections, leaves, tasks, and system-wide operations.

## Core Admin Features

### 1. User Management

#### Get All Users
```bash
GET /admin/users?page=1&limit=20&search=john&role=user&is_active=true

Response:
{
  "success": true,
  "data": {
    "items": [...],
    "total": 150,
    "page": 1,
    "limit": 20
  }
}
```

#### Get User by ID
```bash
GET /admin/users/{user_id}
```

#### Update User
```bash
PUT /admin/users/{user_id}
{
  "full_name": "John Doe Updated",
  "department": "Engineering",
  "position": "Senior Developer",
  "is_active": true
}
```

#### Delete User
```bash
DELETE /admin/users/{user_id}
```
- Soft delete (sets `is_active = false`)
- Preserves all historical data

#### Reset User Password
```bash
POST /admin/users/{user_id}/reset-password
{
  "new_password": "TempPassword123"
}
```
- Admin can reset any user's password
- Useful for account recovery

### 2. Tracker Management

#### View All Trackers
```bash
GET /admin/tracker/all?page=1&limit=50&user_id=5&status=completed

Filters:
- user_id: Filter by specific user
- start_date: From date
- end_date: To date
- status: active/paused/completed
```

#### View User's Trackers
```bash
GET /admin/tracker/user/{user_id}?start_date=2024-02-01&end_date=2024-02-13
```

#### Manual Tracker Adjustment
```bash
PUT /admin/tracker/{tracker_id}
{
  "clock_in": "2024-02-13T09:00:00",
  "clock_out": "2024-02-13T18:00:00",
  "notes": "Adjusted by admin due to system error"
}
```

#### Delete Tracker
```bash
DELETE /admin/tracker/{tracker_id}
```
- Permanently deletes tracker entry
- Use with caution

### 3. Time Correction Management

#### View All Correction Requests
```bash
GET /admin/time-corrections/all?status=pending&page=1&limit=20

Statuses:
- pending: Awaiting review
- approved: Already approved
- rejected: Already rejected
- all: Show everything
```

#### Approve Correction
```bash
POST /admin/time-corrections/{request_id}/approve
{
  "admin_notes": "Verified with manager, approved"
}
```
- Automatically updates tracker
- Logs the action
- Notifies employee (if configured)

#### Reject Correction
```bash
POST /admin/time-corrections/{request_id}/reject
{
  "admin_notes": "Insufficient evidence provided"
}
```

### 4. Leave Management

#### View All Leave Requests
```bash
GET /admin/leaves/all?status=pending&page=1&limit=20
```

#### Approve Leave
```bash
POST /admin/leaves/{leave_id}/approve
{
  "admin_notes": "Approved"
}
```

#### Reject Leave
```bash
POST /admin/leaves/{leave_id}/reject
{
  "admin_notes": "Insufficient leave balance"
}
```

### 5. Task Management

#### Create Task
```bash
POST /admin/tasks
{
  "user_id": 5,
  "name": "Complete Q1 Report",
  "description": "Prepare quarterly sales report",
  "due_date": "2024-02-20T17:00:00",
  "priority": "high",
  "status": "pending"
}
```

#### Assign Task to User
```bash
POST /admin/tasks/{task_id}/assign
{
  "user_id": 5
}
```

#### Update Task Status
```bash
PUT /admin/tasks/{task_id}/status
{
  "status": "in_progress"
}
```

### 6. Reports & Analytics

#### Work Hours Report
```bash
GET /admin/reports/work-hours?start_date=2024-02-01&end_date=2024-02-13&user_id=5

Response:
{
  "success": true,
  "data": {
    "total_hours": 80,
    "average_per_day": 8,
    "by_date": [
      {"date": "2024-02-01", "hours": 8.5},
      {"date": "2024-02-02", "hours": 7.5}
    ]
  }
}
```

#### Attendance Summary
```bash
GET /admin/reports/attendance?month=2&year=2024

Response:
{
  "present": 20,
  "absent": 2,
  "on_leave": 3,
  "late_arrivals": 5
}
```

#### Leave Balance Report
```bash
GET /admin/reports/leave-balance?user_id=5
```

### 7. System Operations

#### View System Logs
```bash
GET /admin/logs?log_type=error&start_date=2024-02-01&limit=100
```

#### Manual Clock-Out All Users
```bash
POST /admin/operations/clock-out-all
{
  "reason": "End of day manual trigger"
}
```
- Useful for system maintenance
- Logs the operation

#### Database Cleanup
```bash
POST /admin/operations/cleanup
{
  "delete_old_logs": true,
  "days_to_keep": 90
}
```

## Access Control

### Admin vs Super Admin
- **Admin**: Can manage users, approve requests, view reports
- **Super Admin**: Same as admin + system operations, delete operations

### Permission Checks
```python
# In app/auth.py
def get_current_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
```

## Dashboard Statistics

Common admin dashboard queries:

### Today's Stats
```python
# Active employees right now
active_count = count(trackers where status='active' and date=today)

# Total hours worked today
total_hours = sum(total_work_seconds for all completed trackers today)

# Pending requests
pending_corrections = count(time_corrections where status='pending')
pending_leaves = count(leaves where status='pending')
```

### Monthly Stats
```python
# Attendance rate
total_working_days = count(business days in month)
total_present = count(distinct user_ids with trackers)
attendance_rate = (total_present / (total_employees * total_working_days)) * 100

# Average work hours
average_hours = avg(total_work_seconds) / 3600
```

## Bulk Operations

### Bulk User Update
```bash
POST /admin/users/bulk-update
{
  "user_ids": [1, 2, 3, 4, 5],
  "updates": {
    "department": "Engineering"
  }
}
```

### Bulk Leave Approval
```bash
POST /admin/leaves/bulk-approve
{
  "leave_ids": [10, 11, 12],
  "admin_notes": "Bulk approved for holidays"
}
```

## Audit Trail

All admin actions are logged:

| Action | Logged Data |
|--------|-------------|
| User update | Old values → New values |
| Password reset | Admin ID, User ID, Timestamp |
| Tracker adjustment | Original → Modified values |
| Approval/Rejection | Request ID, Decision, Notes |

## Error Handling

| Error | Status Code | Condition |
|-------|-------------|-----------|
| Forbidden | 403 | Non-admin accessing admin endpoints |
| Not Found | 404 | Resource doesn't exist |
| Conflict | 409 | Action not allowed (e.g., approve approved request) |
| Bad Request | 400 | Invalid data provided |

## Best Practices

1. **Always add admin notes** when approving/rejecting requests
2. **Use filters** to reduce data load on dashboards
3. **Verify before manual adjustments** - they bypass normal validations
4. **Regular backup** before bulk operations
5. **Monitor audit logs** for suspicious activity

## UI Components

### Admin Dashboard Layout
```
┌─────────────────────────────────────┐
│ Statistics Cards                     │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐│
│ │Active│ │Hours │ │Pend. │ │Users ││
│ └──────┘ └──────┘ └──────┘ └──────┘│
├─────────────────────────────────────┤
│ Pending Approvals                    │
│ • Time Corrections (5)               │
│ • Leave Requests (3)                 │
├─────────────────────────────────────┤
│ Recent Activity                      │
│ • User X clocked in at 9:00 AM      │
│ • Request Y approved                 │
└─────────────────────────────────────┘
```

### Request Review Interface
```
┌─────────────────────────────────────┐
│ Time Correction Request #456        │
├─────────────────────────────────────┤
│ Employee: John Doe                  │
│ Date: 2024-02-13                    │
│ Type: Missed Punch                  │
│                                      │
│ Before          │  After             │
│ Clock In: 9:30  │  9:00             │
│ Clock Out: 17:45│  18:00            │
│                                      │
│ Reason: "Forgot to clock in..."     │
│                                      │
│ Admin Notes: [________________]     │
│ [Approve] [Reject]                  │
└─────────────────────────────────────┘
```

## Related Files

- [`app/routes/admin.py`](file:///d:/SP/HRMS/Backend/app/routes/admin.py) - Main admin endpoints
- [`app/auth.py`](file:///d:/SP/HRMS/Backend/app/auth.py) - Admin authorization
- [Time Corrections](file:///d:/SP/HRMS/Backend/Project_Info/Time_Corrections.md) - Correction workflow
- [Tracker Module](file:///d:/SP/HRMS/Backend/Project_Info/tracker.md) - Tracker management
