# Time Tracker Module

**File**: [`app/routes/tracker.py`](file:///d:/SP/HRMS/Backend/app/routes/tracker.py)  
**Model**: [`TimeTracker`](file:///d:/SP/HRMS/Backend/app/models.py#L354-L390)  
**Scheduler**: [`app/scheduler.py`](file:///d:/SP/HRMS/Backend/app/scheduler.py)

## Overview

The Time Tracker module manages employee work time tracking including clock in/out, break management, and work time calculations.

## Key Concepts

### Tracker Status
- **ACTIVE**: Currently working (clocked in)
- **PAUSED**: On break
- **COMPLETED**: Clocked out for the day

### Work Time Calculation
```
Total Work Time = (Clock Out - Clock In) - Total Pause Time
```

## Core Features

### 1. Clock In
- **Endpoint**: `POST /tracker/clock-in`
- **Description**: Start a new work session
- **Rules**:
  - Only one active session per user per day
  - Creates new tracker with status `ACTIVE`
  - Records clock-in timestamp

**Example**:
```bash
POST /tracker/clock-in

Response:
{
  "success": true,
  "message": "Clocked in successfully at 09:00 AM",
  "data": {
    "id": 123,
    "clock_in": "2024-02-13T09:00:00",
    "status": "active",
    "date": "2024-02-13"
  }
}
```

### 2. Pause (Break Start)
- **Endpoint**: `POST /tracker/pause`
- **Description**: Start a break period
- **Rules**:
  - Must be in ACTIVE status
  - Records pause start time
  - Changes status to PAUSED

**Example**:
```bash
POST /tracker/pause

Response:
{
  "success": true,
  "message": "Break started",
  "data": {
    "pause_periods": [
      {"start": "2024-02-13T12:00:00", "end": null}
    ]
  }
}
```

### 3. Resume (Break End)
- **Endpoint**: `POST /tracker/resume`
- **Description**: End break and resume work
- **Rules**:
  - Must be in PAUSED status
  - Records pause end time
  - Changes status to ACTIVE

**Example**:
```bash
POST /tracker/resume

Response:
{
  "success": true,
  "message": "Resumed work",
  "data": {
    "pause_periods": [
      {"start": "2024-02-13T12:00:00", "end": "2024-02-13T12:30:00"}
    ]
  }
}
```

### 4. Clock Out
- **Endpoint**: `POST /tracker/clock-out`
- **Description**: End work session
- **Rules**:
  - Must be in ACTIVE or PAUSED status
  - If PAUSED, automatically ends the break
  - Records clock-out timestamp
  - Changes status to COMPLETED
  - Calculates total work time

**Example**:
```bash
POST /tracker/clock-out

Response:
{
  "success": true,
  "message": "Clocked out successfully",
  "data": {
    "clock_out": "2024-02-13T18:00:00",
    "total_work_seconds": 28800,  // 8 hours
    "hours_worked": "8h 0m"
  }
}
```

### 5. Get Current Session
- **Endpoint**: `GET /tracker/current-session`
- **Description**: Get current active/paused session
- **Returns**: Current tracker with live work time

**Example**:
```bash
GET /tracker/current-session

Response:
{
  "success": true,
  "data": {
    "id": 123,
    "status": "active",
    "clock_in": "2024-02-13T09:00:00",
    "current_work_seconds": 14400,  // 4 hours so far
    "hours_worked": "4h 0m"
  }
}
```

### 6. Get Work History
- **Endpoint**: `GET /tracker/my-history`
- **Query Params**:
  - `start_date`: Filter by start date
  - `end_date`: Filter by end date
  - `status_filter`: Filter by status (active/paused/completed)

**Example**:
```bash
GET /tracker/my-history?start_date=2024-02-01&end_date=2024-02-13

Response:
{
  "success": true,
  "data": [
    {
      "id": 123,
      "date": "2024-02-13",
      "clock_in": "2024-02-13T09:00:00",
      "clock_out": "2024-02-13T18:00:00",
      "total_work_seconds": 28800,
      "hours_worked": "8h 0m",
      "status": "completed"
    }
  ]
}
```

### 7. Get Trackers by Date
- **Endpoint**: `GET /tracker/by-date?date=2024-02-13`
- **Description**: Get all tracker entries for a specific date
- **Use Case**: Useful for time correction when multiple entries exist

### 8. Delete Tracker
- **Endpoint**: `DELETE /tracker/{tracker_id}`
- **Description**: Delete a tracker entry
- **Rules**: User can only delete their own entries

## Database Model

### TimeTracker Model
```python
class TimeTracker(Base):
    id: int
    user_id: int (FK to users)
    date: Date
    clock_in: datetime
    clock_out: Optional[datetime]
    total_work_seconds: int (default: 0)
    pause_periods: Text (JSON string)
    notes: Optional[str]
    status: TrackerStatus (active/paused/completed)
    created_at: datetime
    updated_at: datetime
    
    # Relationships
    user: User
```

### Pause Periods Format
Stored as JSON string:
```json
[
  {
    "start": "2024-02-13T12:00:00",
    "end": "2024-02-13T12:30:00"
  },
  {
    "start": "2024-02-13T15:00:00",
    "end": "2024-02-13T15:15:00"
  }
]
```

## Work Time Calculation Logic

Located in `calculate_work_time()` function:

```python
def calculate_work_time(
    clock_in: datetime,
    clock_out: Optional[datetime],
    pause_periods: List[dict],
    current_time: Optional[datetime] = None
) -> Tuple[int, int]:
    """
    Returns: (total_work_seconds, total_pause_seconds)
    """
```

### Algorithm:
1. Calculate total time: `clock_out - clock_in`
2. Calculate total pause time from all pause periods
3. Subtract pause time from total time
4. Handle edge cases:
   - Active pauses (no end time yet)
   - Overlapping pauses
   - Invalid pause periods

## Auto Clock-Out Feature

**File**: [`app/scheduler.py`](file:///d:/SP/HRMS/Backend/app/scheduler.py)

### Behavior:
- Runs daily at **11:00 PM IST**
- Automatically clocks out all active trackers
- Ends any active break periods
- Calculates final work time
- Logs the operation

### Configuration:
```python
# In scheduler.py
CLOCK_OUT_HOUR = 23  # 11 PM
CLOCK_OUT_MINUTE = 0
```

## Admin Features

Admin-specific tracker endpoints are in [`app/routes/admin.py`](file:///d:/SP/HRMS/Backend/app/routes/admin.py):

- View all trackers (with pagination and filters)
- View specific user's trackers
- Manual tracker adjustments
- Generate reports

## Time Correction Integration

When time corrections are approved, the tracker entries are automatically updated:

- Missed Clock In → Updates `clock_in` time
- Missed Clock Out → Updates `clock_out` time
- Missed Punch → Updates both times
- Break Resume → Updates pause periods

See: [Time Corrections Documentation](file:///d:/SP/HRMS/Backend/Project_Info/Time_Corrections.md)

## Error Handling

| Error | Condition |
|-------|-----------|
| "Already clocked in" | Trying to clock in when already active |
| "No active session" | Trying to pause/resume without clocking in |
| "Already paused" | Trying to pause when already paused |
| "Not paused" | Trying to resume when not paused |
| "No active session to clock out" | Trying to clock out without clocking in |

## Best Practices

1. **Always check current session** before user actions
2. **Handle timezone properly** - All times stored in UTC, display in IST
3. **Validate pause periods** - Ensure no overlaps or invalid ranges
4. **Log all operations** - For audit trail
5. **Auto-save regularly** - In case of browser crash

## Related Files

- [`app/routes/tracker.py`](file:///d:/SP/HRMS/Backend/app/routes/tracker.py) - Main tracker endpoints
- [`app/routes/admin.py`](file:///d:/SP/HRMS/Backend/app/routes/admin.py) - Admin tracker features
- [`app/scheduler.py`](file:///d:/SP/HRMS/Backend/app/scheduler.py) - Auto clock-out
- [`app/models.py`](file:///d:/SP/HRMS/Backend/app/models.py#L354-L390) - TimeTracker model
- [Time Corrections](file:///d:/SP/HRMS/Backend/Project_Info/Time_Corrections.md) - Correction workflow
