# Task Management API Documentation

## Overview
The Task Management API allows employees to create, manage, and track their tasks, while administrators can view and monitor all employee tasks across the organization.

## Features
- ✅ Employee task creation and management
- ✅ Task status tracking (Pending, In Progress, Completed, Cancelled)
- ✅ Priority and category assignment
- ✅ Due date management
- ✅ Task summary and statistics
- ✅ Admin oversight of all employee tasks
- ✅ Soft delete functionality

## API Endpoints

### Employee Task Management

#### 1. Create Task
**POST** `/tasks/`

Creates a new task for the authenticated user.

**Request Body:**
```json
{
  "name": "Complete project documentation",
  "description": "Write comprehensive documentation for the HRMS project",
  "due_date": "2024-01-15",
  "priority": "high",
  "category": "work"
}
```

**Response:**
```json
{
  "id": 1,
  "user_id": 2,
  "name": "Complete project documentation",
  "description": "Write comprehensive documentation for the HRMS project",
  "status": "pending",
  "due_date": "2024-01-15T00:00:00Z",
  "priority": "high",
  "category": "work",
  "completed_at": null,
  "is_active": true,
  "created_at": "2024-01-08T10:30:00Z",
  "updated_at": null,
  "user": {
    "id": 2,
    "name": "John Doe",
    "email": "john@example.com"
  }
}
```

#### 2. Get My Tasks
**GET** `/tasks/my-tasks`

Retrieves all tasks for the authenticated user with optional filtering.

**Query Parameters:**
- `status` (optional): Filter by task status (pending, in_progress, completed, cancelled)
- `priority` (optional): Filter by priority (low, medium, high, urgent)
- `category` (optional): Filter by category
- `overdue_only` (optional): Show only overdue tasks (boolean)

**Example:**
```
GET /tasks/my-tasks?status=pending&priority=high&overdue_only=true
```

#### 3. Get Task Summary
**GET** `/tasks/my-tasks/summary`

Returns a summary of task statistics for the authenticated user.

**Response:**
```json
{
  "total_tasks": 15,
  "pending_tasks": 5,
  "in_progress_tasks": 3,
  "completed_tasks": 6,
  "cancelled_tasks": 1,
  "overdue_tasks": 2
}
```

#### 4. Get Specific Task
**GET** `/tasks/{task_id}`

Retrieves a specific task by ID.

#### 5. Update Task
**PUT** `/tasks/{task_id}`

Updates a specific task. Only the task owner can update their tasks.

**Request Body:**
```json
{
  "name": "Updated task name",
  "description": "Updated description",
  "status": "in_progress",
  "priority": "medium",
  "category": "personal"
}
```

**Note:** When status is changed to "completed", the `completed_at` field is automatically set to the current timestamp.

#### 6. Delete Task
**DELETE** `/tasks/{task_id}`

Soft deletes a task (sets `is_active` to false). Only the task owner can delete their tasks.

### Admin Task Management

#### 7. Get All Tasks (Admin)
**GET** `/tasks/admin/all-tasks`

Retrieves all tasks across all users. Requires admin or super admin privileges.

**Query Parameters:**
- `status` (optional): Filter by task status
- `priority` (optional): Filter by priority
- `category` (optional): Filter by category
- `user_id` (optional): Filter by specific user ID
- `overdue_only` (optional): Show only overdue tasks
- `offset` (optional): Pagination offset (default: 0)
- `limit` (optional): Number of results per page (default: 10, max: 100)

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "name": "Complete project documentation",
      "description": "Write comprehensive documentation",
      "status": "pending",
      "priority": "high",
      "category": "work",
      "due_date": "2024-01-15T00:00:00Z",
      "completed_at": null,
      "created_at": "2024-01-08T10:30:00Z",
      "updated_at": null,
      "user": {
        "id": 2,
        "name": "John Doe",
        "email": "john@example.com",
        "designation": "Software Developer"
      }
    }
  ],
  "total": 25,
  "offset": 0,
  "limit": 10
}
```

#### 8. Get Admin Task Summary
**GET** `/tasks/admin/summary`

Returns a summary of task statistics across all users. Requires admin or super admin privileges.

**Response:**
```json
{
  "total_tasks": 150,
  "pending_tasks": 45,
  "in_progress_tasks": 30,
  "completed_tasks": 70,
  "cancelled_tasks": 5,
  "overdue_tasks": 12
}
```

## Data Models

### Task Model
```python
class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    priority = Column(String, nullable=True, default="medium")
    category = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### Task Status Enum
```python
class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
```

## Priority Levels
- `low`: Low priority tasks
- `medium`: Medium priority tasks (default)
- `high`: High priority tasks
- `urgent`: Urgent tasks requiring immediate attention

## Category Examples
- `work`: Work-related tasks
- `personal`: Personal tasks
- `project`: Project-specific tasks
- `meeting`: Meeting-related tasks
- `training`: Training and development tasks

## Authentication
All endpoints require authentication using JWT tokens. Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
  "detail": "Access denied. Admin privileges required."
}
```

### 404 Not Found
```json
{
  "detail": "Task not found"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Usage Examples

### Creating a Task
```python
import requests

# Authentication
login_data = {"email": "user@example.com", "password": "password"}
response = requests.post("http://localhost:8000/auth/login", json=login_data)
token = response.json()["access_token"]

# Create task
headers = {"Authorization": f"Bearer {token}"}
task_data = {
    "name": "Review code changes",
    "description": "Review and approve pending pull requests",
    "due_date": "2024-01-10",
    "priority": "high",
    "category": "work"
}

response = requests.post("http://localhost:8000/tasks/", json=task_data, headers=headers)
task = response.json()
```

### Getting Tasks with Filters
```python
# Get only pending high-priority tasks
response = requests.get(
    "http://localhost:8000/tasks/my-tasks",
    params={"status": "pending", "priority": "high"},
    headers=headers
)
tasks = response.json()
```

### Updating Task Status
```python
# Mark task as completed
update_data = {"status": "completed"}
response = requests.put(
    f"http://localhost:8000/tasks/{task_id}",
    json=update_data,
    headers=headers
)
```

## Database Migration

To add the Task table to your database, run the migration:

```bash
# Generate migration
alembic revision --autogenerate -m "Add Task model"

# Apply migration
alembic upgrade head
```

## Testing

Use the provided test script to verify API functionality:

```bash
python test_task_api.py
```

Make sure to update the test credentials in the script before running.

## Security Considerations

1. **Authentication**: All endpoints require valid JWT tokens
2. **Authorization**: Users can only access their own tasks unless they are admin/super admin
3. **Soft Delete**: Tasks are soft deleted to maintain data integrity
4. **Input Validation**: All input data is validated using Pydantic schemas
5. **SQL Injection Protection**: Using SQLAlchemy ORM prevents SQL injection attacks

## Performance Optimizations

1. **Database Indexes**: Optimized indexes for common query patterns
2. **Pagination**: Admin endpoints support pagination for large datasets
3. **Selective Loading**: User relationships are loaded only when needed
4. **Query Optimization**: Efficient queries with proper filtering and sorting

## Future Enhancements

- Task assignment to other users
- Task dependencies and subtasks
- File attachments for tasks
- Task templates
- Automated task reminders
- Task time tracking
- Task comments and collaboration features
