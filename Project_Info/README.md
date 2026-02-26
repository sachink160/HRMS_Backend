# HRMS (Human Resource Management System) - Backend

## 📋 Project Overview

This is a comprehensive **Human Resource Management System (HRMS)** backend built with **FastAPI**, **SQLAlchemy**, and **PostgreSQL**. The system provides complete employee management, time tracking, leave management, task assignment, and administrative features.

## 🏗️ Project Structure

```
Backend/
├── app/
│   ├── routes/              # API endpoints organized by feature
│   │   ├── auth.py         # Authentication & user management
│   │   ├── admin.py        # Admin-only operations
│   │   ├── tracker.py      # Time tracking (clock in/out)
│   │   ├── time_corrections.py  # Time correction requests
│   │   ├── employees.py    # Employee profile management
│   │   ├── tasks.py        # Task assignment & tracking
│   │   ├── holidays.py     # Holiday management
│   │   ├── leaves.py       # Leave requests & approvals
│   │   ├── email.py        # Email configuration
│   │   ├── users.py        # User CRUD operations
│   │   └── logs.py         # System logs
│   ├── models.py           # Database models (SQLAlchemy ORM)
│   ├── schemas.py          # Pydantic schemas for validation
│   ├── database.py         # Database connection & session management
│   ├── auth.py             # JWT authentication & authorization
│   ├── email_service.py    # Email sending service
│   ├── scheduler.py        # Background tasks (auto clock-out, etc.)
│   ├── logger.py           # Logging configuration
│   └── response.py         # Standard API response format
├── migrations/             # Database migration scripts
├── templates/              # Email HTML templates
├── uploads/                # User uploaded files (documents, images)
├── Project_Info/           # 📚 Detailed documentation for each module
├── requirements.txt        # Python dependencies
└── .env                    # Environment variables (database, secrets)
```

## 🚀 Key Features

### 1. **Authentication & Authorization**
- JWT-based authentication
- Role-based access control (Admin & User)
- Password reset via email
- Admin creation with secret code

### 2. **Time Tracking**
- Clock in/out functionality
- Pause/resume work sessions
- Auto clock-out at end of day
- View work history with filters

### 3. **Time Corrections**
- Request corrections for missed punches
- Admin approval/rejection workflow
- Support for multiple correction types (Missed Punch, Break Resume, etc.)

### 4. **Leave Management**
- Submit leave requests
- Admin approval workflow
- Leave balance tracking

### 5. **Task Management**
- Assign tasks to employees
- Track task status (Pending, In Progress, Completed)
- Task history and reporting

### 6. **Employee Management**
- Profile management
- Employment history
- Document uploads
- Department & position tracking

### 7. **Holidays**
- Centralized holiday management
- Mark company-wide holidays

### 8. **Email Integration**
- Configurable SMTP settings
- Template-based emails
- Email logs for tracking

## 🗄️ Database Models

The system uses the following main database models (defined in [`models.py`](file:///d:/SP/HRMS/Backend/app/models.py)):

| Model | Description |
|-------|-------------|
| `User` | Core user model with authentication & profile info |
| `TimeTracker` | Clock in/out records with pause periods |
| `TimeCorrectionRequest` | Requests for time corrections |
| `TimeCorrectionLog` | Audit log for time corrections |
| `Leave` | Leave requests and approvals |
| `Task` | Task assignments |
| `Holiday` | Company holidays |
| `EmploymentHistory` | Employment history records |
| `EmailSettings` | SMTP configuration |
| `EmailTemplate` | Email templates |
| `EmailLog` | Sent email logs |
| `PasswordResetToken` | Password reset tokens |
| `Log` | System logs |

## 🔌 API Routes

All API routes are organized in the [`app/routes/`](file:///d:/SP/HRMS/Backend/app/routes) directory:

| Route File | Base Path | Description |
|------------|-----------|-------------|
| [`auth.py`](file:///d:/SP/HRMS/Backend/app/routes/auth.py) | `/auth` | Login, register, password reset |
| [`admin.py`](file:///d:/SP/HRMS/Backend/app/routes/admin.py) | `/admin` | Admin-only operations |
| [`tracker.py`](file:///d:/SP/HRMS/Backend/app/routes/tracker.py) | `/tracker` | Time tracking endpoints |
| [`time_corrections.py`](file:///d:/SP/HRMS/Backend/app/routes/time_corrections.py) | `/time-corrections` | Time correction requests |
| [`employees.py`](file:///d:/SP/HRMS/Backend/app/routes/employees.py) | `/employees` | Employee management |
| [`tasks.py`](file:///d:/SP/HRMS/Backend/app/routes/tasks.py) | `/tasks` | Task management |
| [`holidays.py`](file:///d:/SP/HRMS/Backend/app/routes/holidays.py) | `/holidays` | Holiday management |
| [`leaves.py`](file:///d:/SP/HRMS/Backend/app/routes/leaves.py) | `/leaves` | Leave requests |
| [`email.py`](file:///d:/SP/HRMS/Backend/app/routes/email.py) | `/email` | Email configuration |
| [`users.py`](file:///d:/SP/HRMS/Backend/app/routes/users.py) | `/users` | User CRUD |
| [`logs.py`](file:///d:/SP/HRMS/Backend/app/routes/logs.py) | `/logs` | System logs |

## 📚 Detailed Documentation

For detailed information about each module, see the documentation files in [`Project_Info/`](file:///d:/SP/HRMS/Backend/Project_Info):

- [**Authentication**](file:///d:/SP/HRMS/Backend/Project_Info/authentication.md) - Login, registration, JWT, password reset
- [**Admin Features**](file:///d:/SP/HRMS/Backend/Project_Info/admin.md) - Admin-only operations and management
- [**Time Tracker**](file:///d:/SP/HRMS/Backend/Project_Info/tracker.md) - Clock in/out, pause/resume, work time calculation
- [**Time Corrections**](file:///d:/SP/HRMS/Backend/Project_Info/Time_Corrections.md) - Correction request workflow
- [**Tasks**](file:///d:/SP/HRMS/Backend/Project_Info/tasks.md) - Task assignment and tracking
- [**User Management**](file:///d:/SP/HRMS/Backend/Project_Info/user.md) - User profiles and roles
- [**Employees**](file:///d:/SP/HRMS/Backend/Project_Info/employees.md) - Employee records and history
- [**Holidays**](file:///d:/SP/HRMS/Backend/Project_Info/holiday.md) - Holiday management
- [**Email Management**](file:///d:/SP/HRMS/Backend/Project_Info/email_management.md) - Email configuration and templates

## 🛠️ Technology Stack

- **Framework**: FastAPI (Async Python web framework)
- **Database**: PostgreSQL (with async SQLAlchemy)
- **Authentication**: JWT (JSON Web Tokens)
- **ORM**: SQLAlchemy 2.0 (Async)
- **Email**: SMTP with template support
- **Scheduler**: APScheduler (for background tasks)
- **Validation**: Pydantic v2
- **Migrations**: Custom migration scripts + Alembic

## ⚙️ Configuration

Environment variables are stored in `.env` file:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost/hrms

# JWT
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Admin Setup
ADMIN_SECRET_CODE=your-admin-code

# Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- PostgreSQL 12+

### Installation

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run migrations**:
   ```bash
   python run_migration.py
   ```

4. **Create super admin** (optional):
   ```bash
   python create_super_admin.py
   ```

5. **Run the application**:
   ```bash
   uvicorn app.main:app --reload
   ```

6. **Access API documentation**:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## 🔄 Background Tasks

The system uses APScheduler ([`scheduler.py`](file:///d:/SP/HRMS/Backend/app/scheduler.py)) for:
- **Auto Clock-Out**: Automatically clocks out users at 11:00 PM IST
- **Email Notifications**: Sends scheduled emails
- **Data Cleanup**: Periodic cleanup of old logs

## 🔐 Security Features

- Password hashing with bcrypt
- JWT token authentication
- Role-based access control (RBAC)
- Token expiration and refresh
- Password reset with time-limited tokens
- SQL injection prevention via ORM

## 📊 API Response Format

All API responses follow a standard format (defined in [`response.py`](file:///d:/SP/HRMS/Backend/app/response.py)):

```json
{
  "success": true,
  "message": "Operation successful",
  "data": {...}
}
```

## 🧪 Testing

- Test files are prefixed with `test_`
- Run tests: `pytest`

## 📝 Logging

- Logs are stored in `logs/` directory
- Configurable log levels
- Centralized logging via [`logger.py`](file:///d:/SP/HRMS/Backend/app/logger.py)

## 🤝 Contributing

1. Follow the existing code structure
2. Add proper docstrings to functions
3. Update relevant documentation in `Project_Info/`
4. Test your changes before committing

## 📞 Support

For questions or issues, please refer to the detailed documentation in the `Project_Info/` directory.
