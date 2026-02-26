# Employees Module

**File**: [`app/routes/employees.py`](file:///d:/SP/HRMS/Backend/app/routes/employees.py)  
**Model**: [`EmploymentHistory`](file:///d:/SP/HRMS/Backend/app/models.py#L250-L297)

## Overview

The Employees module manages employment records, history, and profile documents.

## Features

### 1. Employment History

Track employment changes over time:
- Promotions
- Department transfers
- Role changes
- Manager changes
- Salary adjustments

#### Add Employment Record
```bash
POST /employees/{user_id}/employment-history
{
  "position_title": "Senior Developer",
  "department": "Engineering",
  "start_date": "2024-01-01",
  "salary": 75000.00,
  "manager_id": 3,
  "is_current": true
}

Response:
{
  "success": true,
  "message": "Employment record added",
  "data": {
    "id": 50,
    "position_title": "Senior Developer",
    "is_current": true
  }
}
```

#### Get Employment History
```bash
GET /employees/{user_id}/employment-history

Response:
{
  "success": true,
  "data": [
    {
      "id": 50,
      "position_title": "Senior Developer",
      "department": "Engineering",
      "start_date": "2024-01-01",
      "is_current": true,
      "manager": {
        "id": 3,
        "name": "Jane Manager"
      }
    },
    {
      "id": 49,
      "position_title": "Junior Developer",
      "department": "Engineering",
      "start_date": "2022-01-01",
      "end_date": "2023-12-31",
      "is_current": false
    }
  ]
}
```

### 2. Document Management

Upload and manage employee documents:
- Resume/CV
- Certificates
- ID documents
- Contracts

#### Upload Document
```bash
POST /employees/{user_id}/documents
Content-Type: multipart/form-data

{
  "file": <file>,
  "document_type": "certificate",
  "title": "AWS Certification",
  "description": "AWS Solutions Architect"
}

Response:
{
  "success": true,
  "message": "Document uploaded",
  "data": {
    "id": 100,
    "filename": "aws_cert_12345.pdf",
    "document_type": "certificate",
    "upload_date": "2024-02-13T10:00:00"
  }
}
```

#### Get Documents
```bash
GET /employees/{user_id}/documents

Response:
{
  "success": true,
  "data": [
    {
      "id": 100,
      "filename": "aws_cert_12345.pdf",
      "document_type": "certificate",
      "title": "AWS Certification",
      "status": "approved",
      "upload_date": "2024-02-13T10:00:00"
    }
  ]
}
```

#### Download Document
```bash
GET /employees/documents/{document_id}/download
```
- Returns file with appropriate content type
- Access control: User can only download own documents (or admin)

### 3. Employee Profile Summary

```bash
GET /employees/{user_id}/profile

Response:
{
  "success": true,
  "data": {
    "user": {
      "id": 5,
      "full_name": "John Doe",
      "email": "john@example.com",
      "department": "Engineering",
      "position": "Senior Developer"
    },
    "current_employment": {
      "position_title": "Senior Developer",
      "department": "Engineering",
      "start_date": "2024-01-01",
      "manager": "Jane Manager"
    },
    "employment_history_count": 3,
    "documents_count": 5
  }
}
```

## Database Models

### EmploymentHistory
```python
class EmploymentHistory(Base):
    id: int
    user_id: int
    position_title: str
    department: str
    start_date: date
    end_date: Optional[date]
    is_current: bool (default: False)
    salary: Optional[Numeric(10, 2)]
    employment_type: Optional[str]  # full-time, part-time, contract
    manager_id: Optional[int]
    location: Optional[str]
    responsibilities: Optional[Text]
    notes: Optional[Text]
    created_at: datetime
    updated_at: datetime
```

### Document Model (if implemented)
```python
class EmployeeDocument(Base):
    id: int
    user_id: int
    filename: str
    original_filename: str
    document_type: str  # resume, certificate, id, contract
    title: str
    description: Optional[str]
    file_path: str
    file_size: int
    mime_type: str
    status: DocumentStatus  # pending/approved/rejected
    upload_date: datetime
    approved_by: Optional[int]
    approved_at: Optional[datetime]
```

## Document Types

- **resume**: CV/Resume
- **certificate**: Educational/Professional certificates
- **id**: Identity documents (passport, driver's license)
- **contract**: Employment contract
- **other**: Miscellaneous documents

## Document Status Workflow

```
Uploaded → Pending → Admin Review → Approved/Rejected
```

## Validation Rules

### Employment History
- ✅ `start_date` required
- ✅ `end_date` must be after `start_date`
- ✅ Only one record can have `is_current = true`
- ✅ When adding new current record, previous current is auto-ended

### Documents
- ✅ File size limit: 5MB
- ✅ Allowed formats: PDF, JPG, PNG, DOCX
- ✅ Virus scan (if implemented)
- ✅ User can only upload to own profile

## File Storage

Documents stored in:
```
uploads/
  ├── user_{user_id}/
  │   ├── documents/
  │   │   ├── {document_id}_{filename}.pdf
  │   │   └── ...
  │   └── profile/
  │       └── avatar.jpg
```

## Security

- ✅ Files stored outside web root
- ✅ Unique filenames (prevent overwrites)
- ✅ Access control checks before download
- ✅ MIME type validation
- ✅ File extension whitelist

## Admin Features

### Approve/Reject Documents
```bash
POST /admin/employees/documents/{document_id}/approve
POST /admin/employees/documents/{document_id}/reject
{
  "notes": "Reason for rejection"
}
```

### Bulk Operations
```bash
# Update all employees in department
POST /admin/employees/bulk-update
{
  "filter": {"department": "Engineering"},
  "updates": {"location": "Remote"}
}
```

## Reports

### Employment Timeline
```bash
GET /employees/{user_id}/timeline

Response: Chronological list of all employment changes
```

### Organizational Chart
```bash
GET /employees/org-chart

Response: Hierarchical structure based on manager relationships
```

## Best Practices

1. **Keep history accurate** - Record all changes
2. **Document everything** - Upload relevant certificates
3. **Regular reviews** - Update employment records annually
4. **Privacy** - Salary info should be restricted
5. **Retention policy** - Define document retention rules

## Related Files

- [`app/routes/employees.py`](file:///d:/SP/HRMS/Backend/app/routes/employees.py) - Employee endpoints
- [`app/models.py`](file:///d:/SP/HRMS/Backend/app/models.py#L250-L297) - EmploymentHistory model
- [User Management](file:///d:/SP/HRMS/Backend/Project_Info/user.md) - Related user info
