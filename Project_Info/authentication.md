# Authentication Module

**File**: [`app/routes/auth.py`](file:///d:/SP/HRMS/Backend/app/routes/auth.py)  
**Models**: [`User`](file:///d:/SP/HRMS/Backend/app/models.py), `PasswordResetToken`

## Overview

The authentication module handles all user authentication, registration, login, and password management functionality.

## Key Features

### 1. User Registration
- **Endpoint**: `POST /auth/register`
- Registers new employees
- Validates email uniqueness
- Hashes passwords securely
- Creates user with default role

### 2. Admin Registration
- **Endpoint**: `POST /auth/register-admin` (Admin only)
- **Endpoint**: `POST /auth/create-admin-with-secret` (Public with secret code)
- Creates admin users
- Requires either existing admin authentication or secret code
- Secret code from environment variable `ADMIN_SECRET_CODE`

### 3. Login
- **Endpoint**: `POST /auth/login`
- Authenticates user with email/password
- Returns JWT access token
- Token expires based on `ACCESS_TOKEN_EXPIRE_MINUTES` env variable

### 4. Logout
- **Endpoint**: `POST /auth/logout`
- Logs out current user
- Client should delete stored token

### 5. Profile Management
- **Get Profile**: `GET /auth/profile`
- **Update Profile**: `PUT /auth/profile`
- Update name, phone, department, position, etc.

### 6. Password Management
- **Change Password**: `POST /auth/change-password`
- Requires current password verification
- Works for both employees and admins

### 7. Password Reset Flow

#### Step 1: Request Reset
- **Endpoint**: `POST /auth/forgot-password`
- User provides email
- System sends reset link via email
- Always returns success (security best practice)

#### Step 2: Verify Token
- **Endpoint**: `GET /auth/verify-reset-token?token={token}`
- Validates token before showing reset form
- Checks expiration and usage status

#### Step 3: Reset Password
- **Endpoint**: `POST /auth/reset-password`
- Provides token and new password
- Marks token as used
- Updates user password

## JWT Authentication

### Token Generation
```python
# Located in app/auth.py
create_access_token(data: dict, expires_delta: timedelta)
```

### Token Verification
```python
# Located in app/auth.py
get_current_user(token: str, db: AsyncSession)
get_current_admin_user(current_user: User)
```

### Token Structure
```json
{
  "sub": "user@email.com",
  "exp": 1234567890
}
```

## Database Models

### User Model
```python
class User(Base):
    id: int
    email: str (unique)
    hashed_password: str
    full_name: str
    phone: Optional[str]
    role: UserRole (user/admin)
    department: Optional[str]
    position: Optional[str]
    date_of_birth: Optional[date]
    address: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

### PasswordResetToken Model
```python
class PasswordResetToken(Base):
    id: int
    user_id: int
    token: str (unique)
    expires_at: datetime
    is_used: bool
    created_at: datetime
```

## Pydantic Schemas

Defined in [`app/schemas.py`](file:///d:/SP/HRMS/Backend/app/schemas.py):

- `UserCreate` - User registration
- `UserLogin` - Login credentials
- `UserUpdate` - Profile updates
- `PasswordChange` - Password change
- `ForgotPasswordRequest` - Password reset request
- `ResetPasswordRequest` - Password reset
- `AdminCreateWithSecret` - Admin creation with secret

## Security Features

### Password Hashing
- Uses **bcrypt** algorithm
- Salt rounds: 12 (configurable)
- Implemented in `app/auth.py`

### Token Security
- JWT tokens with expiration
- Reset tokens expire after 1 hour
- Single-use reset tokens
- Token validation before use

### Access Control
- Role-based authorization
- Admin-only endpoints protected
- User can only access own resources

## Email Integration

Password reset emails are sent via the email service:

```python
from app.email_service import send_password_reset_email

await send_password_reset_email(
    to_email=user.email,
    user_name=user.full_name,
    reset_link=reset_link
)
```

## Error Handling

Common error responses:

| Error | Status Code | Description |
|-------|-------------|-------------|
| Invalid credentials | 401 | Wrong email/password |
| Email already exists | 400 | Duplicate email on registration |
| Invalid token | 400 | Expired or invalid reset token |
| Unauthorized | 401 | Missing or invalid JWT token |
| Forbidden | 403 | Insufficient permissions |

## Usage Examples

### Register User
```bash
POST /auth/register
{
  "email": "user@example.com",
  "password": "SecurePassword123",
  "full_name": "John Doe",
  "phone": "+1234567890"
}
```

### Login
```bash
POST /auth/login
{
  "email": "user@example.com",
  "password": "SecurePassword123"
}

Response:
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access_token": "eyJhbGc...",
    "token_type": "bearer",
    "user": {...}
  }
}
```

### Password Reset
```bash
# Step 1: Request reset
POST /auth/forgot-password
{
  "email": "user@example.com"
}

# Step 2: User clicks link in email
GET /auth/verify-reset-token?token=abc123

# Step 3: Reset password
POST /auth/reset-password
{
  "token": "abc123",
  "new_password": "NewSecurePassword123"
}
```

## Related Files

- [`app/auth.py`](file:///d:/SP/HRMS/Backend/app/auth.py) - JWT utilities
- [`app/models.py`](file:///d:/SP/HRMS/Backend/app/models.py#L23-L142) - User model
- [`app/schemas.py`](file:///d:/SP/HRMS/Backend/app/schemas.py) - Validation schemas
- [`app/email_service.py`](file:///d:/SP/HRMS/Backend/app/email_service.py) - Email sending
