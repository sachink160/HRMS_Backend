# Email Management Module

**File**: [`app/routes/email.py`](file:///d:/SP/HRMS/Backend/app/routes/email.py)  
**Service**: [`app/email_service.py`](file:///d:/SP/HRMS/Backend/app/email_service.py)  
**Models**: [`EmailSettings`](file:///d:/SP/HRMS/Backend/app/models.py#L189-L208), `EmailTemplate`, `EmailLog`

## Overview

The Email Management module handles SMTP configuration, email templates, and email sending functionality.

## Components

### 1. Email Settings (SMTP Configuration)

#### Get Settings (Admin)
```bash
GET /email/settings

Response:
{
  "success": true,
  "data": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_username": "noreply@company.com",
    "use_tls": true,
    "from_email": "noreply@company.com",
    "from_name": "HRMS System"
  }
}
```

#### Update Settings (Admin)
```bash
PUT /email/settings
{
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "smtp_username": "noreply@company.com",
  "smtp_password": "app-password-here",
  "use_tls": true,
  "from_email": "noreply@company.com",
  "from_name": "HRMS System"
}
```

#### Test Email (Admin)
```bash
POST /email/test
{
  "to_email": "admin@company.com"
}

Response:
{
  "success": true,
  "message": "Test email sent successfully"
}
```

### 2. Email Templates

Pre-defined templates for common emails:

#### Template Types
- `password_reset` - Password reset email
- `welcome` - New user welcome email
- `leave_approved` - Leave approval notification
- `leave_rejected` - Leave rejection notification
- `task_assigned` - New task assignment

#### Get Templates (Admin)
```bash
GET /email/templates

Response:
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "password_reset",
      "subject": "Reset Your Password",
      "template_type": "password_reset",
      "html_content": "<html>...",
      "is_active": true
    }
  ]
}
```

#### Update Template (Admin)
```bash
PUT /email/templates/{template_id}
{
  "subject": "Updated Subject",
  "html_content": "<html>...</html>"
}
```

### 3. Email Logs

Track all sent emails for auditing:

```bash
GET /email/logs?page=1&limit=50&status=sent

Response:
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 100,
        "recipient_email": "user@example.com",
        "recipient_name": "John Doe",
        "subject": "Password Reset Request",
        "template_type": "password_reset",
        "status": "sent",
        "sent_at": "2024-02-13T10:00:00",
        "error_message": null
      }
    ],
    "total": 150
  }
}
```

## Database Models

### EmailSettings
```python
class EmailSettings(Base):
    id: int
    smtp_server: str
    smtp_port: int
    smtp_username: str
    smtp_password: str (encrypted)
    use_tls: bool (default: True)
    from_email: str
    from_name: str
    is_active: bool (default: True)
    created_at: datetime
    updated_at: datetime
```

### EmailTemplate
```python
class EmailTemplate(Base):
    id: int
    name: str (unique)
    subject: str
    html_content: Text
    text_content: Optional[Text]
    template_type: str
    is_active: bool (default: True)
    created_at: datetime
    updated_at: datetime
```

### EmailLog
```python
class EmailLog(Base):
    id: int
    recipient_email: str
    recipient_name: Optional[str]
    subject: str
    template_type: str
    status: str  # sent, failed
    sent_at: Optional[datetime]
    error_message: Optional[Text]
    created_at: datetime
```

## Email Service Functions

Located in [`app/email_service.py`](file:///d:/SP/HRMS/Backend/app/email_service.py):

```python
async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    to_name: Optional[str] = None
) -> bool:
    """Send email using configured SMTP settings"""

async def send_password_reset_email(
    to_email: str,
    user_name: str,
    reset_link: str
) -> bool:
    """Send password reset email with template"""

async def send_welcome_email(
    to_email: str,
    user_name: str
) -> bool:
    """Send welcome email to new user"""
```

## Template Variables

Templates support variable substitution:

```html
<html>
  <body>
    <p>Hello {{user_name}},</p>
    <p>Click here to reset your password:</p>
    <a href="{{reset_link}}">Reset Password</a>
  </body>
</html>
```

Variables replaced at send time:
- `{{user_name}}` → Actual user name
- `{{reset_link}}` → Generated reset link
- `{{company_name}}` → Company name from settings

## Email Status

- **sent**: Email delivered successfully
- **failed**: Delivery failed (see error_message)
- **pending**: Queued for sending (if using async queue)

## Security

- ✅ SMTP password encrypted in database
- ✅ TLS/SSL support for secure transmission
- ✅ Email logs for auditing
- ✅ Rate limiting to prevent spam
- ✅ Admin-only access to settings

## Gmail Setup Example

For Gmail with 2FA:

1. Enable 2-Factor Authentication
2. Generate App Password
3. Use these settings:
   ```
   SMTP Server: smtp.gmail.com
   Port: 587
   Username: your-email@gmail.com
   Password: [16-character app password]
   Use TLS: Yes
   ```

## Error Handling

Common email errors:

| Error | Cause | Solution |
|-------|-------|----------|
| Authentication failed | Wrong credentials | Check username/password |
| Connection timeout | Wrong server/port | Verify SMTP settings |
| TLS error | SSL/TLS mismatch | Check TLS settings |
| Recipient rejected | Invalid email | Validate email format |

## Best Practices

1. **Test thoroughly** - Use test endpoint before production
2. **Monitor logs** - Check for failed emails
3. **Template carefully** - Test with different clients
4. **Secure credentials** - Never expose SMTP password
5. **Backup templates** - Keep original templates safe

## Related Files

- [`app/routes/email.py`](file:///d:/SP/HRMS/Backend/app/routes/email.py) - Email management endpoints
- [`app/email_service.py`](file:///d:/SP/HRMS/Backend/app/email_service.py) - Email sending service
- [`app/models.py`](file:///d:/SP/HRMS/Backend/app/models.py#L189-L247) - Email models
- [`templates/`](file:///d:/SP/HRMS/Backend/templates) - HTML email templates
