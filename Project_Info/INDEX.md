# HRMS Project - Complete Documentation Index

**Welcome to the HRMS (Human Resource Management System) Documentation!**

This comprehensive guide will help you understand the entire HRMS project structure, features, and implementation details.

## 📚 Documentation Structure

### 1. **[README](file:///d:/SP/HRMS/Backend/Project_Info/README.md)** - Start Here!
- Project overview
- Technology stack
- Installation guide
- Quick start
- System architecture

---

## 🔐 Core Modules

### 2. **[Authentication](file:///d:/SP/HRMS/Backend/Project_Info/authentication.md)**
**File**: [`app/routes/auth.py`](file:///d:/SP/HRMS/Backend/app/routes/auth.py)

Learn about:
- User registration and login
- JWT token authentication
- Password reset flow
- Admin creation
- Role-based access control

**Key Endpoints**:
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login
- `POST /auth/forgot-password` - Password reset request
- `GET /auth/profile` - Get user profile

---

### 3. **[User Management](file:///d:/SP/HRMS/Backend/Project_Info/user.md)**
**File**: [`app/routes/users.py`](file:///d:/SP/HRMS/Backend/app/routes/users.py)

Learn about:
- User CRUD operations
- User roles (Admin/User)
- Profile management
- User activation/deactivation

**Key Endpoints**:
- `GET /users` - Get all users (admin)
- `PUT /users/{id}` - Update user
- `DELETE /users/{id}` - Deactivate user

---

## ⏰ Time Management

### 4. **[Time Tracker](file:///d:/SP/HRMS/Backend/Project_Info/tracker.md)**
**File**: [`app/routes/tracker.py`](file:///d:/SP/HRMS/Backend/app/routes/tracker.py)

Learn about:
- Clock in/out functionality
- Pause/resume (break management)
- Work time calculation
- Auto clock-out feature
- Tracking history

**Key Endpoints**:
- `POST /tracker/clock-in` - Start work
- `POST /tracker/pause` - Start break
- `POST /tracker/resume` - End break
- `POST /tracker/clock-out` - End work
- `GET /tracker/current-session` - Get active session

**Related**: 
- [`app/scheduler.py`](file:///d:/SP/HRMS/Backend/app/scheduler.py) - Auto clock-out at 11 PM

---

### 5. **[Time Corrections](file:///d:/SP/HRMS/Backend/Project_Info/Time_Corrections.md)**
**File**: [`app/routes/time_corrections.py`](file:///d:/SP/HRMS/Backend/app/routes/time_corrections.py)

Learn about:
- Correction request types (Missed Punch, Break Resume)
- Request-approval workflow
- Admin review process
- Automatic tracker updates

**Key Endpoints**:
- `POST /time-corrections/request` - Submit correction
- `GET /time-corrections/my-requests` - View my requests
- `POST /admin/time-corrections/{id}/approve` - Approve (admin)
- `POST /admin/time-corrections/{id}/reject` - Reject (admin)

---

## 👥 Employee Management

### 6. **[Employees](file:///d:/SP/HRMS/Backend/Project_Info/employees.md)**
**File**: [`app/routes/employees.py`](file:///d:/SP/HRMS/Backend/app/routes/employees.py)

Learn about:
- Employment history tracking
- Document management
- Profile information
- Career progression

**Key Features**:
- Employment record management
- Document upload/download
- Organizational hierarchy

---

### 7. **[Tasks](file:///d:/SP/HRMS/Backend/Project_Info/tasks.md)**
**File**: [`app/routes/tasks.py`](file:///d:/SP/HRMS/Backend/app/routes/tasks.py)

Learn about:
- Task assignment
- Task lifecycle (Pending → In Progress → Completed)
- Priority management
- Due date tracking

**Key Endpoints**:
- `POST /tasks` - Create task (admin)
- `GET /tasks/my-tasks` - Get my tasks
- `PUT /tasks/{id}/status` - Update task status

---

### 8. **[Leaves](file:///d:/SP/HRMS/Backend/Project_Info/leaves.md)**
**File**: [`app/routes/leaves.py`](file:///d:/SP/HRMS/Backend/app/routes/leaves.py)

Learn about:
- Leave request submission
- Leave types (vacation, sick, personal)
- Admin approval workflow
- Leave balance tracking

**Key Endpoints**:
- `POST /leaves/request` - Submit leave request
- `GET /leaves/my-leaves` - View my leaves
- `POST /admin/leaves/{id}/approve` - Approve leave (admin)

---

## ⚙️ System Management

### 9. **[Admin Features](file:///d:/SP/HRMS/Backend/Project_Info/admin.md)**
**File**: [`app/routes/admin.py`](file:///d:/SP/HRMS/Backend/app/routes/admin.py)

Learn about:
- User management (admin)
- Tracker oversight
- Request approvals
- Reports and analytics
- Bulk operations

**Admin Capabilities**:
- Manage all users
- Review and approve requests
- Generate reports
- System operations

---

### 10. **[Holidays](file:///d:/SP/HRMS/Backend/Project_Info/holiday.md)**
**File**: [`app/routes/holidays.py`](file:///d:/SP/HRMS/Backend/app/routes/holidays.py)

Learn about:
- Company holiday management
- Holiday calendar
- Integration with leave system

---

### 11. **[Email Management](file:///d:/SP/HRMS/Backend/Project_Info/email_management.md)**
**File**: [`app/routes/email.py`](file:///d:/SP/HRMS/Backend/app/routes/email.py)

Learn about:
- SMTP configuration
- Email templates
- Password reset emails
- Email logs and tracking

---

## 🗂️ Database & Models

### 12. **[Database Models](file:///d:/SP/HRMS/Backend/app/models.py)**

All database models defined using SQLAlchemy ORM:

| Model | Description | Lines |
|-------|-------------|-------|
| `User` | User accounts and profiles | 23-142 |
| `TimeTracker` | Time tracking records | 354-390 |
| `TimeCorrectionRequest` | Time correction requests | 446-490 |
| `TimeCorrectionLog` | Correction audit logs | 492-519 |
| `Leave` | Leave requests | 144-168 |
| `Task` | Task assignments | 305-343 |
| `Holiday` | Company holidays | 170-186 |
| `EmploymentHistory` | Employment records | 250-297 |
| `EmailSettings` | SMTP configuration | 189-208 |
| `EmailTemplate` | Email templates | 210-226 |
| `EmailLog` | Email sending logs | 228-247 |
| `PasswordResetToken` | Password reset tokens | 418-439 |
| `Log` | System logs | 392-416 |

---

## 🔗 Quick Reference

### Common Workflows

#### Employee Daily Flow
```
1. Clock In    → POST /tracker/clock-in
2. Start Break → POST /tracker/pause
3. End Break   → POST /tracker/resume
4. Clock Out   → POST /tracker/clock-out
```

#### Time Correction Flow
```
1. Employee: Submit Request → POST /time-corrections/request
2. Admin: Review → GET /admin/time-corrections/all
3. Admin: Approve/Reject → POST /admin/time-corrections/{id}/approve
4. System: Update Tracker automatically
```

#### Leave Request Flow
```
1. Employee: Submit Leave → POST /leaves/request
2. Admin: Review → GET /admin/leaves/all
3. Admin: Approve/Reject → POST /admin/leaves/{id}/approve
```

### Authentication Flow
```
1. Register → POST /auth/register
2. Login → POST /auth/login (receive JWT token)
3. Use Token → Include in Authorization header for all requests
   Header: Authorization: Bearer {token}
```

### File Locations

| Component | Location |
|-----------|----------|
| API Routes | [`Backend/app/routes/`](file:///d:/SP/HRMS/Backend/app/routes) |
| Models | [`Backend/app/models.py`](file:///d:/SP/HRMS/Backend/app/models.py) |
| Schemas | [`Backend/app/schemas.py`](file:///d:/SP/HRMS/Backend/app/schemas.py) |
| Database | [`Backend/app/database.py`](file:///d:/SP/HRMS/Backend/app/database.py) |
| Auth Logic | [`Backend/app/auth.py`](file:///d:/SP/HRMS/Backend/app/auth.py) |
| Email Service | [`Backend/app/email_service.py`](file:///d:/SP/HRMS/Backend/app/email_service.py) |
| Scheduler | [`Backend/app/scheduler.py`](file:///d:/SP/HRMS/Backend/app/scheduler.py) |
| Migrations | [`Backend/migrations/`](file:///d:/SP/HRMS/Backend/migrations) |
| Documentation | [`Backend/Project_Info/`](file:///d:/SP/HRMS/Backend/Project_Info) |

---

## 🎯 Getting Started Guide

### For New Developers

1. **Start with [README](file:///d:/SP/HRMS/Backend/Project_Info/README.md)** - Understand the project
2. **Read [Authentication](file:///d:/SP/HRMS/Backend/Project_Info/authentication.md)** - Learn security model
3. **Review [Time Tracker](file:///d:/SP/HRMS/Backend/Project_Info/tracker.md)** - Core feature
4. **Study [Admin Features](file:///d:/SP/HRMS/Backend/Project_Info/admin.md)** - Management capabilities
5. **Explore the codebase** - Start with routes you'll be working on

### For Frontend Developers

Key endpoints to integrate:
- Authentication: Login, register, password reset
- Tracker: Clock in/out, current session
- User Profile: Get/update profile
- Tasks: My tasks, update status
- Leaves: Submit request, view status

### For System Administrators

Focus on:
- [Admin Features](file:///d:/SP/HRMS/Backend/Project_Info/admin.md) - All admin capabilities
- [Email Management](file:///d:/SP/HRMS/Backend/Project_Info/email_management.md) - SMTP setup
- Database configuration and backups
- User management and permissions

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────┐
│          Frontend (React/Vue/etc)           │
└──────────────────┬──────────────────────────┘
                   │ HTTP/REST API
┌──────────────────▼──────────────────────────┐
│           FastAPI Backend                   │
│  ┌──────────────────────────────────────┐  │
│  │  Routes (API Endpoints)              │  │
│  │  - auth.py, tracker.py, admin.py     │  │
│  └─────────────┬────────────────────────┘  │
│  ┌─────────────▼────────────────────────┐  │
│  │  Business Logic & Services           │  │
│  │  - auth.py, email_service.py         │  │
│  └─────────────┬────────────────────────┘  │
│  ┌─────────────▼────────────────────────┐  │
│  │  Database Layer (SQLAlchemy ORM)     │  │
│  │  - models.py, database.py            │  │
│  └─────────────┬────────────────────────┘  │
└────────────────┼──────────────────────────┘
                 │
┌────────────────▼──────────────────────────┐
│     PostgreSQL Database                   │
│  - Users, Trackers, Leaves, Tasks, etc.  │
└───────────────────────────────────────────┘

        Background Services
┌───────────────────────────────────────────┐
│  APScheduler (scheduler.py)               │
│  - Auto clock-out (11 PM daily)           │
│  - Email notifications                     │
└───────────────────────────────────────────┘
```

---

## 💡 Tips

- 📖 **Start with README** for complete setup instructions
- 🔍 **Use Ctrl+F** to search within documentation
- 📝 **Update docs** when making changes
- 🔗 **Click file links** to view source code
- ❓ **Ask questions** if something is unclear

---

## 🆘 Need Help?

1. Check the specific module documentation
2. Review the source code files (linked in each doc)
3. Check the API documentation at `/docs` (Swagger UI)
4. Review database models in [`models.py`](file:///d:/SP/HRMS/Backend/app/models.py)

---

**Last Updated**: February 2024  
**Version**: 1.0
