# Employee Tracker API Documentation

This document describes all employee tracker endpoints available in the HRMS system. All endpoints require authentication via Bearer token.

**Base URL:** `/tracker`

**Authentication:** All endpoints require a valid JWT token in the Authorization header:
```
Authorization: Bearer <token>
```

---

## 1. Clock In

Start a new tracking session for the current day.

**Endpoint:** `POST /tracker/clock-in`

**Description:** Creates a new time tracking session for the authenticated user. Only one active session is allowed per day. If the user already has an active or paused session, the request will fail.

**Request Body:** None

**Query Parameters:** None

**Response:**

**Success (201 Created):**
```json
{
  "status": "success",
  "message": "Clocked in successfully",
  "data": {
    "id": 1,
    "user_id": 5,
    "date": "2025-01-15",
    "clock_in": "2025-01-15T09:00:00+00:00",
    "clock_out": null,
    "status": "active",
    "pause_periods": [],
    "total_work_seconds": 0,
    "total_pause_seconds": 0,
    "total_work_hours": null,
    "created_at": "2025-01-15T09:00:00+00:00",
    "updated_at": "2025-01-15T09:00:00+00:00"
  }
}
```

**Error (400 Bad Request):**
```json
{
  "status": "error",
  "message": "You already have an active tracking session. Please clock out first.",
  "data": {}
}
```

**Error (500 Internal Server Error):**
```json
{
  "status": "error",
  "message": "Failed to clock in",
  "data": {}
}
```

---

## 2. Pause Session

Pause the current active tracking session.

**Endpoint:** `POST /tracker/pause`

**Description:** Pauses the current active tracking session. The session status changes from "active" to "paused". A pause period is recorded with a start time. The pause can be resumed later using the resume endpoint.

**Request Body:** None

**Query Parameters:** None

**Response:**

**Success (200 OK):**
```json
{
  "status": "success",
  "message": "Session paused successfully",
  "data": {
    "id": 1,
    "user_id": 5,
    "date": "2025-01-15",
    "clock_in": "2025-01-15T09:00:00+00:00",
    "clock_out": null,
    "status": "paused",
    "pause_periods": [
      {
        "pause_start": "2025-01-15T10:30:00+00:00",
        "pause_end": null
      }
    ],
    "total_work_seconds": 5400,
    "total_pause_seconds": 0,
    "total_work_hours": 1.5,
    "created_at": "2025-01-15T09:00:00+00:00",
    "updated_at": "2025-01-15T10:30:00+00:00"
  }
}
```

**Error (400 Bad Request):**
```json
{
  "status": "error",
  "message": "No active session found. Please clock in first.",
  "data": {}
}
```

**Error (400 Bad Request):**
```json
{
  "status": "error",
  "message": "Session is already paused. Please resume first.",
  "data": {}
}
```

**Error (500 Internal Server Error):**
```json
{
  "status": "error",
  "message": "Failed to pause session",
  "data": {}
}
```

---

## 3. Resume Session

Resume a paused tracking session.

**Endpoint:** `POST /tracker/resume`

**Description:** Resumes a paused tracking session. The session status changes from "paused" to "active". The open pause period is closed with an end time.

**Request Body:** None

**Query Parameters:** None

**Response:**

**Success (200 OK):**
```json
{
  "status": "success",
  "message": "Session resumed successfully",
  "data": {
    "id": 1,
    "user_id": 5,
    "date": "2025-01-15",
    "clock_in": "2025-01-15T09:00:00+00:00",
    "clock_out": null,
    "status": "active",
    "pause_periods": [
      {
        "pause_start": "2025-01-15T10:30:00+00:00",
        "pause_end": "2025-01-15T11:00:00+00:00"
      }
    ],
    "total_work_seconds": 5400,
    "total_pause_seconds": 1800,
    "total_work_hours": 1.5,
    "created_at": "2025-01-15T09:00:00+00:00",
    "updated_at": "2025-01-15T11:00:00+00:00"
  }
}
```

**Error (400 Bad Request):**
```json
{
  "status": "error",
  "message": "No paused session found. Please clock in first.",
  "data": {}
}
```

**Error (400 Bad Request):**
```json
{
  "status": "error",
  "message": "Session is not paused. Please pause first.",
  "data": {}
}
```

**Error (500 Internal Server Error):**
```json
{
  "status": "error",
  "message": "Failed to resume session",
  "data": {}
}
```

---

## 4. Clock Out

End the current tracking session.

**Endpoint:** `POST /tracker/clock-out`

**Description:** Ends the current active or paused tracking session. The session status changes to "completed". Any open pause periods are automatically closed. Final work time and pause time are calculated and stored.

**Request Body:** None

**Query Parameters:** None

**Response:**

**Success (200 OK):**
```json
{
  "status": "success",
  "message": "Clocked out successfully",
  "data": {
    "id": 1,
    "user_id": 5,
    "date": "2025-01-15",
    "clock_in": "2025-01-15T09:00:00+00:00",
    "clock_out": "2025-01-15T18:00:00+00:00",
    "status": "completed",
    "pause_periods": [
      {
        "pause_start": "2025-01-15T12:00:00+00:00",
        "pause_end": "2025-01-15T13:00:00+00:00"
      }
    ],
    "total_work_seconds": 28800,
    "total_pause_seconds": 3600,
    "total_work_hours": 8.0,
    "created_at": "2025-01-15T09:00:00+00:00",
    "updated_at": "2025-01-15T18:00:00+00:00"
  }
}
```

**Error (400 Bad Request):**
```json
{
  "status": "error",
  "message": "No active session found. Please clock in first.",
  "data": {}
}
```

**Error (500 Internal Server Error):**
```json
{
  "status": "error",
  "message": "Failed to clock out",
  "data": {}
}
```

---

## 5. Get Current Session

Get the current active or paused session status.

**Endpoint:** `GET /tracker/current`

**Description:** Retrieves the current active or paused tracking session for today. Returns detailed information including current work time and pause time calculations. If no active session exists, returns a response indicating no active session.

**Request Body:** None

**Query Parameters:** None

**Response:**

**Success (200 OK) - With Active Session:**
```json
{
  "status": "success",
  "message": "Current session retrieved successfully",
  "data": {
    "has_active_session": true,
    "tracker": {
      "id": 1,
      "user_id": 5,
      "date": "2025-01-15",
      "clock_in": "2025-01-15T09:00:00+00:00",
      "clock_out": null,
      "status": "active",
      "pause_periods": [
        {
          "pause_start": "2025-01-15T12:00:00+00:00",
          "pause_end": "2025-01-15T13:00:00+00:00"
        }
      ],
      "total_work_seconds": 10800,
      "total_pause_seconds": 3600,
      "total_work_hours": 3.0,
      "created_at": "2025-01-15T09:00:00+00:00",
      "updated_at": "2025-01-15T13:00:00+00:00"
    },
    "current_work_seconds": 10800,
    "current_pause_seconds": 3600
  }
}
```

**Success (200 OK) - No Active Session:**
```json
{
  "status": "success",
  "message": "No active session",
  "data": {
    "has_active_session": false,
    "tracker": null,
    "current_work_seconds": null,
    "current_pause_seconds": null
  }
}
```

**Error (500 Internal Server Error):**
```json
{
  "status": "error",
  "message": "Failed to get current session",
  "data": {}
}
```

---

## 6. Get My History

Get the employee's own tracking history with filtering and pagination.

**Endpoint:** `GET /tracker/my-history`

**Description:** Retrieves the authenticated user's tracking history. Supports filtering by date range and status, with pagination support. Results are ordered by date (descending) and creation time (descending).

**Request Body:** None

**Query Parameters:**

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `start_date` | date | No | Filter records from this date (inclusive) | `2025-01-01` |
| `end_date` | date | No | Filter records until this date (inclusive) | `2025-01-31` |
| `status_filter` | string | No | Filter by status: `active`, `paused`, or `completed` | `completed` |
| `offset` | integer | No | Number of records to skip (default: 0, min: 0) | `0` |
| `limit` | integer | No | Maximum number of records to return (default: 10, min: 1, max: 100) | `20` |

**Response:**

**Success (200 OK):**
```json
{
  "status": "success",
  "message": "Tracking history retrieved successfully",
  "data": {
    "items": [
      {
        "id": 1,
        "user_id": 5,
        "date": "2025-01-15",
        "clock_in": "2025-01-15T09:00:00+00:00",
        "clock_out": "2025-01-15T18:00:00+00:00",
        "status": "completed",
        "pause_periods": [
          {
            "pause_start": "2025-01-15T12:00:00+00:00",
            "pause_end": "2025-01-15T13:00:00+00:00"
          }
        ],
        "total_work_seconds": 28800,
        "total_pause_seconds": 3600,
        "total_work_hours": 8.0,
        "created_at": "2025-01-15T09:00:00+00:00",
        "updated_at": "2025-01-15T18:00:00+00:00"
      },
      {
        "id": 2,
        "user_id": 5,
        "date": "2025-01-14",
        "clock_in": "2025-01-14T09:00:00+00:00",
        "clock_out": "2025-01-14T17:30:00+00:00",
        "status": "completed",
        "pause_periods": [],
        "total_work_seconds": 30600,
        "total_pause_seconds": 0,
        "total_work_hours": 8.5,
        "created_at": "2025-01-14T09:00:00+00:00",
        "updated_at": "2025-01-14T17:30:00+00:00"
      }
    ],
    "total": 2,
    "offset": 0,
    "limit": 10
  }
}
```

**Error (500 Internal Server Error):**
```json
{
  "status": "error",
  "message": "Failed to fetch tracking history",
  "data": {}
}
```

---

## Response Data Structures

### Tracker Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Unique tracker record ID |
| `user_id` | integer | ID of the user who owns this tracker |
| `date` | string (ISO date) | Date of the tracking session (YYYY-MM-DD) |
| `clock_in` | string (ISO datetime) | Clock-in timestamp in UTC |
| `clock_out` | string (ISO datetime) | Clock-out timestamp in UTC (null if session is active/paused) |
| `status` | string | Session status: `active`, `paused`, or `completed` |
| `pause_periods` | array | List of pause periods with start and end times |
| `total_work_seconds` | integer | Total work time in seconds (excluding pause time) |
| `total_pause_seconds` | integer | Total pause time in seconds |
| `total_work_hours` | float | Total work time in hours (calculated from seconds) |
| `created_at` | string (ISO datetime) | Record creation timestamp |
| `updated_at` | string (ISO datetime) | Last update timestamp |

### Pause Period Object

| Field | Type | Description |
|-------|------|-------------|
| `pause_start` | string (ISO datetime) | Pause start timestamp |
| `pause_end` | string (ISO datetime) | Pause end timestamp (null if pause is still active) |

---

## Status Values

- **`active`**: Session is currently active and tracking time
- **`paused`**: Session is paused (time is not being tracked)
- **`completed`**: Session has been clocked out and finalized

---

## Notes

1. **Time Calculation**: Work time is calculated as total elapsed time minus pause periods. Pause periods are automatically closed when clocking out.

2. **Single Active Session**: Only one active or paused session is allowed per user per day. Attempting to clock in when an active session exists will result in an error.

3. **Automatic Pause Closure**: When clocking out, any open pause periods are automatically closed using the clock-out time.

4. **Date Filtering**: Date filters use the session date, not the clock-in/clock-out timestamps.

5. **Pagination**: The history endpoint supports pagination with `offset` and `limit` parameters. The default limit is 10 records, with a maximum of 100 records per request.

6. **Timezone**: All timestamps are returned in UTC (ISO 8601 format with timezone).

