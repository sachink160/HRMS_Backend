# API Response Format Standard

This document describes the standardized API response format used across all HRMS backend endpoints.

## Standard Response Format

All API responses follow a consistent structure:

```json
{
  "status": "success" | "error",
  "message": "Human-readable message",
  "data": {
    // Response data (can be any structure: object, array, etc.)
  }
}
```

### Success Response

```json
{
  "status": "success",
  "message": "Operation completed successfully",
  "data": {
    // Your data here
  }
}
```

### Error Response

```json
{
  "status": "error",
  "message": "Error message describing what went wrong",
  "data": {
    // Additional error details (optional)
  },
  "error_code": "ERROR_CODE" // Optional: for programmatic error handling
}
```

## Response Status Codes

The HTTP status codes are used alongside the response format:

- `200 OK` - Success
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

## Examples

### Success - Get User Profile

**Request:**
```
GET /auth/profile
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "Profile retrieved successfully",
  "data": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "role": "user",
    "is_active": true
  }
}
```

### Success - Login

**Request:**
```
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "Login successful",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "email": "user@example.com",
      "name": "John Doe",
      "role": "user"
    }
  }
}
```

### Error - Bad Request

**Request:**
```
POST /auth/register
Content-Type: application/json

{
  "email": "existing@example.com",
  "password": "password123"
}
```

**Response (400 Bad Request):**
```json
{
  "status": "error",
  "message": "Email already registered",
  "data": {}
}
```

### Error - Unauthorized

**Request:**
```
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "wrongpassword"
}
```

**Response (401 Unauthorized):**
```json
{
  "status": "error",
  "message": "Incorrect email or password",
  "data": {},
  "error_code": "UNAUTHORIZED"
}
```

### Error - Validation Error

**Request:**
```
POST /auth/register
Content-Type: application/json

{
  "email": "invalid-email",
  "password": "123"
}
```

**Response (422 Unprocessable Entity):**
```json
{
  "status": "error",
  "message": "Request validation failed",
  "data": {
    "validation_errors": {
      "body.email": "value is not a valid email address",
      "body.password": "ensure this value has at least 8 characters"
    }
  },
  "error_code": "VALIDATION_ERROR"
}
```

## Error Codes

Common error codes used in responses:

- `UNAUTHORIZED` - Authentication required
- `FORBIDDEN` - Insufficient permissions
- `NOT_FOUND` - Resource not found
- `BAD_REQUEST` - Invalid request
- `VALIDATION_ERROR` - Request validation failed
- `INTERNAL_ERROR` - Internal server error

## Implementation

### Backend

Use the `APIResponse` utility class from `app.response`:

```python
from app.response import APIResponse

# Success response
return APIResponse.success(
    data={"key": "value"},
    message="Operation successful"
)

# Error response
return APIResponse.bad_request(message="Invalid input")

# Created response
return APIResponse.created(
    data=new_resource,
    message="Resource created"
)
```

### Frontend

The frontend API client automatically handles the standardized format:

```typescript
// The interceptor extracts the data field automatically
const response = await api.get('/auth/profile');
// response.data contains the actual data (not wrapped in status/message/data)

// Error handling
try {
  await api.post('/auth/login', credentials);
} catch (error) {
  // error.message contains the error message
  // error.data contains additional error data
  console.error(error.message);
}
```

## Migration Notes

- All endpoints now return standardized responses
- The frontend interceptor automatically extracts the `data` field from successful responses
- Error responses are handled consistently across the application
- Legacy error format (`detail` field) is still supported for backward compatibility during migration

