# User Management Module

**File**: [`app/routes/users.py`](file:///d:/SP/HRMS/Backend/app/routes/users.py)  
**Model**: [`User`](file:///d:/SP/HRMS/Backend/app/models.py#L23-L142)

## Overview

User management handles employee profiles, roles, and basic CRUD operations.

## User Roles

### UserRole Enum
- **USER**: Regular employee
- **ADMIN**: Administrator with elevated permissions

## User Model

```python
class User(Base):
    # Authentication
    id: int
    email: str (unique, indexed)
    hashed_password: str
    role: UserRole (default: USER)
    
    # Personal Information
    full_name: str
    phone: Optional[str]
    date_of_birth: Optional[date]
    address: Optional[str]
    
    # Employment Details
    department: Optional[str]
    position: Optional[str]
    join_date: Optional[date]
    employee_id: Optional[str] (unique)
    
    # Status
    is_active: bool (default: True)
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    trackers: List[TimeTracker]
    leaves: List[Leave]
    tasks: List[Task]
    employment_history: List[EmploymentHistory]
```

## Features

### 1. Get All Users (Admin)
```bash
GET /users?page=1&limit=20&search=john&role=user&is_active=true

Filters:
- search: Search by name or email
- role: Filter by user/admin
- is_active: Active/inactive users
- department: Filter by department
```

### 2. Get User by ID
```bash
GET /users/{user_id}

Response:
{
  "success": true,
  "data": {
    "id": 5,
    "email": "john@example.com",
    "full_name": "John Doe",
    "role": "user",
    "department": "Engineering",
    "position": "Developer",
    "is_active": true
  }
}
```

### 3. Update User (Admin)
```bash
PUT /users/{user_id}
{
  "full_name": "John Doe Updated",
  "phone": "+1234567890",
  "department": "Engineering",
  "position": "Senior Developer"
}
```

### 4. Deactivate User (Admin)
```bash
DELETE /users/{user_id}
```
- Soft delete - sets `is_active = false`
- User cannot login but data is preserved
- Can be reactivated later

### 5. Reactivate User (Admin)
```bash
POST /users/{user_id}/reactivate
```

## Employee Self-Service

Users can update their own profile via auth endpoints:
- `GET /auth/profile` - View own profile
- `PUT /auth/profile` - Update own profile
- Limited fields (cannot change role, employee_id, etc.)

## Validation Rules

### Email
- ✅ Must be unique
- ✅ Valid email format
- ✅ Cannot be changed after registration (prevents identity issues)

### Phone
- ✅ Optional
- ✅ Format: +[country code][number]

### Employee ID
- ✅ Unique if provided
- ✅ Usually auto-generated or assigned by admin

### Department & Position
- ✅ Free text (no enum)
- ✅ Consider standardizing for reporting

## User States

### Active User
- `is_active = true`
- Can login and use system
- Appears in user lists

### Inactive User
- `is_active = false`
- Cannot login
- Hidden from default user lists
- Historical data preserved

## Indexes

For performance optimization:

```python
__table_args__ = (
    Index('idx_user_email', 'email'),
    Index('idx_user_active', 'is_active'),
    Index('idx_user_role_active', 'role', 'is_active'),
    Index('idx_user_department', 'department'),
    Index('idx_user_employee_id', 'employee_id'),
)
```

## Related Models

### EmploymentHistory
Tracks employment changes over time:
```python
class EmploymentHistory(Base):
    id: int
    user_id: int
    position_title: str
    department: str
    start_date: date
    end_date: Optional[date]
    is_current: bool
    salary: Optional[Numeric]
    manager_id: Optional[int]
```

## Common Queries

### Active Employees Count
```python
SELECT COUNT(*) FROM users WHERE is_active = true AND role = 'user'
```

### By Department
```python
SELECT department, COUNT(*) 
FROM users 
WHERE is_active = true 
GROUP BY department
```

### Recent Joiners
```python
SELECT * FROM users 
WHERE join_date >= NOW() - INTERVAL '30 days'
ORDER BY join_date DESC
```

## Security Considerations

- ✅ Passwords are hashed with bcrypt
- ✅ JWT tokens for authentication
- ✅ Admin cannot see user passwords
- ✅ Password reset requires email verification
- ✅ Role changes require admin privileges

## Best Practices

1. **Standardize departments** - Use consistent naming
2. **Regular audits** - Review inactive users
3. **Employee IDs** - Use systematic numbering
4. **Data retention** - Never hard delete users
5. **Privacy** - Limit who can see personal info

## Related Files

- [`app/routes/users.py`](file:///d:/SP/HRMS/Backend/app/routes/users.py) - User CRUD endpoints
- [`app/routes/auth.py`](file:///d:/SP/HRMS/Backend/app/routes/auth.py) - Authentication
- [`app/models.py`](file:///d:/SP/HRMS/Backend/app/models.py#L23-L142) - User model
- [Authentication](file:///d:/SP/HRMS/Backend/Project_Info/authentication.md) - Auth details
