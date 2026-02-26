# Time Corrections Module

**File**: [`app/routes/time_corrections.py`](file:///d:/SP/HRMS/Backend/app/routes/time_corrections.py)  
**Models**: [`TimeCorrectionRequest`](file:///d:/SP/HRMS/Backend/app/models.py#L446-L490), [`TimeCorrectionLog`](file:///d:/SP/HRMS/Backend/app/models.py#L492-L519)

## Overview

The Time Corrections module allows employees to request corrections for missed clock in/out times or break issues, with an admin approval workflow.

## Correction Types

### 1. Missed Punch
- **Use Case**: Forgot to clock in or clock out (or both)
- **Fields**: 
  - `corrected_clock_in` (required)
  - `corrected_clock_out` (required)
- **Effect**: Updates both clock in and clock out times

### 2. Took Break but Forgot to Resume
- **Use Case**: Went on break but forgot to click resume
- **Fields**: 
  - `corrected_clock_in` (optional - for extending the break start)
  - `corrected_clock_out` (required - when actually resumed)
- **Effect**: Updates pause periods to reflect actual break time

## Workflow

```
Employee Request → Pending → Admin Review → Approved/Rejected → Update Tracker
```

### Step 1: Employee Creates Request
- **Endpoint**: `POST /time-corrections/request`
- Employee selects date and correction type
- Provides corrected times and reason
- Status: `PENDING`

### Step 2: Admin Reviews
- **Endpoint**: `GET /time-corrections/admin/all` (view all requests)
- Admin filters by status (pending/approved/rejected)
- Views request details with original vs corrected times

### Step 3: Admin Decision
- **Approve**: `POST /time-corrections/admin/{id}/approve`
  - Updates tracker entry with corrected times
  - Creates audit log entry
  - Status: `APPROVED`
  
- **Reject**: `POST /time-corrections/admin/{id}/reject`
  - No tracker changes
  - Creates audit log entry
  - Status: `REJECTED`

### Step 4: Tracker Update (on Approval)
The system automatically updates the tracker based on correction type:

**Missed Punch**:
```python
tracker.clock_in = corrected_clock_in
tracker.clock_out = corrected_clock_out
tracker.total_work_seconds = recalculated
```

**Break Resume**:
```python
# Updates or adds pause period
pause_periods = [
  {
    "start": original_break_start,
    "end": corrected_clock_out  # When actually resumed
  }
]
```

## API Endpoints

### Employee Endpoints

#### 1. Create Correction Request
```bash
POST /time-corrections/request
{
  "request_date": "2024-02-13",
  "issue_type": "Missed Punch",
  "corrected_clock_in": "2024-02-13T09:00:00",
  "corrected_clock_out": "2024-02-13T18:00:00",
  "reason": "Forgot to clock in in the morning"
}

Response:
{
  "success": true,
  "message": "Time correction request submitted",
  "data": {
    "id": 456,
    "status": "pending",
    "created_at": "2024-02-13T10:00:00"
  }
}
```

#### 2. Get My Requests
```bash
GET /time-corrections/my-requests?status=pending

Response:
{
  "success": true,
  "data": [
    {
      "id": 456,
      "request_date": "2024-02-13",
      "issue_type": "Missed Punch",
      "status": "pending",
      "reason": "Forgot to clock in",
      "created_at": "2024-02-13T10:00:00"
    }
  ]
}
```

#### 3. Get Request Details
```bash
GET /time-corrections/{id}

Response:
{
  "success": true,
  "data": {
    "id": 456,
    "request_date": "2024-02-13",
    "issue_type": "Missed Punch",
    "original_clock_in": "2024-02-13T09:30:00",
    "original_clock_out": "2024-02-13T17:45:00",
    "corrected_clock_in": "2024-02-13T09:00:00",
    "corrected_clock_out": "2024-02-13T18:00:00",
    "status": "pending",
    "reason": "Forgot to clock in",
    "tracker_id": 123
  }
}
```

### Admin Endpoints

#### 1. Get All Requests
```bash
GET /time-corrections/admin/all?status=pending&page=1&limit=20

Response:
{
  "success": true,
  "data": {
    "items": [...],
    "total": 50,
    "page": 1,
    "limit": 20
  }
}
```

#### 2. Approve Request
```bash
POST /time-corrections/admin/456/approve
{
  "admin_notes": "Approved after verification"
}

Response:
{
  "success": true,
  "message": "Time correction approved",
  "data": {
    "id": 456,
    "status": "approved",
    "reviewed_by": 1,
    "reviewed_at": "2024-02-13T11:00:00"
  }
}
```

#### 3. Reject Request
```bash
POST /time-corrections/admin/456/reject
{
  "admin_notes": "Insufficient documentation"
}

Response:
{
  "success": true,
  "message": "Time correction rejected"
}
```

## Database Models

### TimeCorrectionRequest
```python
class TimeCorrectionRequest(Base):
    id: int
    user_id: int
    tracker_id: Optional[int]  # Reference to tracker entry
    request_date: date
    issue_type: str  # "Missed Punch" or "Took Break but Forgot to Resume"
    
    # Original times (from tracker)
    original_clock_in: Optional[datetime]
    original_clock_out: Optional[datetime]
    
    # Corrected times (requested by user)
    corrected_clock_in: Optional[datetime]
    corrected_clock_out: Optional[datetime]
    
    reason: str  # Employee's explanation
    admin_notes: Optional[str]  # Admin's comments
    
    status: TimeCorrectionRequestStatus  # pending/approved/rejected
    reviewed_by: Optional[int]  # Admin user ID
    reviewed_at: Optional[datetime]
    
    created_at: datetime
    updated_at: datetime
```

### TimeCorrectionLog
```python
class TimeCorrectionLog(Base):
    id: int
    request_id: int
    action: str  # "created", "approved", "rejected"
    performed_by: int  # User ID
    old_values: Optional[Text]  # JSON of old tracker values
    new_values: Optional[Text]  # JSON of new tracker values
    comments: Optional[str]
    created_at: datetime
```

## Special Cases

### 1. Multiple Trackers on Same Day
- If multiple tracker entries exist for the same date
- User must specify which tracker to correct
- Admin can see all trackers for that date

### 2. No Tracker Exists
- If employee never clocked in
- Request can still be created
- On approval, a new tracker entry is created

### 3. Admin Time Corrections
- Admin can correct their own time
- **Special Rule**: If admin has an active tracker when making self-correction:
  - System pauses/clocks out the active tracker first
  - Then applies the correction
  - This prevents double-counting time

### 4. Break Resume Logic
When approving "Took Break but Forgot to Resume":
```python
# Example: User went on break at 12:00, forgot to resume
# They actually resumed at 1:30 but tracker shows still paused

# Before correction:
pause_periods = [
  {"start": "12:00", "end": null}  # Still paused!
]

# After correction (corrected_clock_out = "13:30"):
pause_periods = [
  {"start": "12:00", "end": "13:30"}  # Break ended
]
```

## Validation Rules

### Request Creation
- ✅ Must have at least one corrected time (clock in or clock out)
- ✅ Corrected times must be on the requested date
- ✅ Clock out must be after clock in
- ✅ Reason must be provided (minimum 10 characters)
- ✅ Cannot request corrections for future dates

### Admin Approval
- ✅ Only pending requests can be approved/rejected
- ✅ Admin cannot approve their own requests (if implemented)
- ✅ Admin notes recommended but optional

## Audit Trail

All actions are logged in `TimeCorrectionLog`:

| Action | Performer | Data Logged |
|--------|-----------|-------------|
| Created | Employee | Original request data |
| Approved | Admin | Old tracker values → New values |
| Rejected | Admin | Reason for rejection |

## UI Flow

### Employee View
1. Click "Request Time Correction"
2. Select date (shows current tracker data if exists)
3. Choose correction type
4. Enter corrected times
5. Provide reason
6. Submit request
7. View status in "My Requests"

### Admin View
1. View all requests (filterable by status)
2. See pending requests highlighted
3. Click request to see details:
   - Original vs corrected times (side-by-side)
   - Employee's reason
   - Related tracker data
4. Add admin notes
5. Approve or Reject

## Error Handling

| Error | Condition |
|-------|-----------|
| "Request already exists" | Duplicate request for same date/type |
| "No tracker found" | Trying to correct non-existent tracker |
| "Invalid time range" | Clock out before clock in |
| "Request already reviewed" | Trying to review approved/rejected request |

## Related Files

- [`app/routes/time_corrections.py`](file:///d:/SP/HRMS/Backend/app/routes/time_corrections.py) - Main endpoints
- [`app/routes/admin.py`](file:///d:/SP/HRMS/Backend/app/routes/admin.py) - Admin review endpoints
- [`app/models.py`](file:///d:/SP/HRMS/Backend/app/models.py#L446-L519) - Database models
- [Tracker Module](file:///d:/SP/HRMS/Backend/Project_Info/tracker.md) - Related tracker docs
