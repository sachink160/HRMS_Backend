# Leave Management Module

**File**: [`app/routes/leaves.py`](file:///d:/SP/HRMS/Backend/app/routes/leaves.py)  
**Model**: [`Leave`](file:///d:/SP/HRMS/Backend/app/models.py#L144-L168)

## Overview

Leave management handles employee leave requests with an admin approval workflow.

## Leave Status

- **PENDING**: Request submitted, awaiting approval
- **APPROVED**: Leave approved by admin
- **REJECTED**: Leave request rejected

## Features

### 1. Submit Leave Request
```bash
POST /leaves/request
{
  "start_date": "2024-02-20T00:00:00",
  "end_date": "2024-02-22T23:59:59",
  "leave_type": "vacation",
  "reason": "Family vacation"
}

Response:
{
  "success": true,
  "message": "Leave request submitted",
  "data": {
    "id": 25,
    "status": "pending",
    "days": 3
  }
}
```

### 2. Get My Leaves
```bash
GET /leaves/my-leaves?status=pending

Response:
{
  "success": true,
  "data": [
    {
      "id": 25,
      "start_date": "2024-02-20",
      "end_date": "2024-02-22",
      "leave_type": "vacation",
      "status": "pending",
      "days": 3,
      "reason": "Family vacation"
    }
  ]
}
```

### 3. Admin Approve/Reject
```bash
POST /admin/leaves/{leave_id}/approve
{
  "admin_notes": "Approved"
}

POST /admin/leaves/{leave_id}/reject
{
  "admin_notes": "Insufficient leave balance"
}
```

## Database Model

```python
class Leave(Base):
    id: int
    user_id: int
    start_date: datetime
    end_date: datetime
    leave_type: str  # vacation, sick, personal
    reason: Text
    status: LeaveStatus  # pending/approved/rejected
    admin_notes: Optional[Text]
    is_active: bool (default: True)
    created_at: datetime
    updated_at: datetime
```

## Related Files

- [`app/routes/leaves.py`](file:///d:/SP/HRMS/Backend/app/routes/leaves.py) - Leave endpoints
- [`app/models.py`](file:///d:/SP/HRMS/Backend/app/models.py#L144-L168) - Leave model
