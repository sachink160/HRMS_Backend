# Tasks Module

**File**: [`app/routes/tasks.py`](file:///d:/SP/HRMS/Backend/app/routes/tasks.py)  
**Model**: [`Task`](file:///d:/SP/HRMS/Backend/app/models.py#L305-L343)

## Overview

The Tasks module enables task assignment, tracking, and management for employees.

## Task Lifecycle

```
Created → Pending → In Progress → Completed
                  ↓
                Cancelled
```

## Task Status

- **PENDING**: Task assigned but not started
- **IN_PROGRESS**: Task currently being worked on
- **COMPLETED**: Task finished
- **CANCELLED**: Task cancelled/no longer needed

## Features

### 1. Create Task (Admin only)
```bash
POST /tasks
{
  "user_id": 5,
  "name": "Prepare Monthly Report",
  "description": "Compile sales data for January 2024",
  "due_date": "2024-02-15T17:00:00",
  "priority": "high",
  "status": "pending"
}

Response:
{
  "success": true,
  "message": "Task created successfully",
  "data": {
    "id": 789,
    "name": "Prepare Monthly Report",
    "status": "pending",
    "assigned_to": "John Doe"
  }
}
```

### 2. Get My Tasks (Employee)
```bash
GET /tasks/my-tasks?status=pending&page=1&limit=20

Response:
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 789,
        "name": "Prepare Monthly Report",
        "description": "Compile sales data...",
        "status": "pending",
        "priority": "high",
        "due_date": "2024-02-15T17:00:00",
        "created_at": "2024-02-01T10:00:00"
      }
    ],
    "total": 5,
    "page": 1,
    "limit": 20
  }
}
```

### 3. Get Task Details
```bash
GET /tasks/{task_id}
```

### 4. Update Task Status
```bash
PUT /tasks/{task_id}/status
{
  "status": "in_progress"
}
```
- Employee can update status of their assigned tasks
- Admin can update any task

### 5. Update Task (Admin only)
```bash
PUT /tasks/{task_id}
{
  "name": "Updated Task Name",
  "description": "Updated description",
  "due_date": "2024-02-20T17:00:00",
  "priority": "medium"
}
```

### 6. Delete Task (Admin only)
```bash
DELETE /tasks/{task_id}
```
- Soft delete (sets `is_active = false`)

### 7. Reassign Task (Admin only)
```bash
PUT /tasks/{task_id}/assign
{
  "user_id": 10
}
```

## Database Model

```python
class Task(Base):
    id: int
    user_id: int  # Assigned user
    name: str
    description: Optional[str]
    status: TaskStatus  # pending/in_progress/completed/cancelled
    priority: Optional[str]  # low/medium/high
    due_date: Optional[datetime]
    completed_at: Optional[datetime]
    is_active: bool (default: True)
    created_at: datetime
    updated_at: datetime
    
    # Relationship
    user: User
```

## Task Priority

- **High**: Urgent, due soon
- **Medium**: Normal priority
- **Low**: Can be done later

Sort order: High → Medium → Low → None

## Filters

### Employee View
- **Status**: pending, in_progress, completed, cancelled
- **Due Date**: Filter by date range
- **Priority**: Filter by priority level

### Admin View
- All employee filters +
- **User**: Filter by assigned user
- **Overdue**: Show tasks past due date

## Notifications (if implemented)

- Task assigned → Email to employee
- Due date approaching → Reminder email
- Task completed → Notification to admin

## Related Endpoints (Admin)

Located in [`admin.py`](file:///d:/SP/HRMS/Backend/app/routes/admin.py):

- `GET /admin/tasks/all` - View all tasks
- `GET /admin/tasks/user/{user_id}` - Tasks for specific user
- `GET /admin/tasks/overdue` - All overdue tasks
- `POST /admin/tasks/bulk-assign` - Assign same task to multiple users

## Best Practices

1. **Clear task names** - Descriptive and actionable
2. **Set realistic due dates** - Consider employee workload
3. **Add detailed descriptions** - Include requirements and resources
4. **Update status regularly** - Keep tracking accurate
5. **Mark completed tasks** - Helps with performance reviews

## Related Files

- [`app/routes/tasks.py`](file:///d:/SP/HRMS/Backend/app/routes/tasks.py) - Task endpoints
- [`app/routes/admin.py`](file:///d:/SP/HRMS/Backend/app/routes/admin.py) - Admin task management
- [`app/models.py`](file:///d:/SP/HRMS/Backend/app/models.py#L305-L343) - Task model
