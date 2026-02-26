# Holiday Management Module

**File**: [`app/routes/holidays.py`](file:///d:/SP/HRMS/Backend/app/routes/holidays.py)  
**Model**: [`Holiday`](file:///d:/SP/HRMS/Backend/app/models.py#L170-L186)

## Overview

The Holiday module manages company-wide holidays that apply to all employees.

## Features

### 1. Get Holidays
```bash
GET /holidays?year=2024&month=2

Response:
{
  "success": true,
  "data": [
    {
      "id": 10,
      "date": "2024-02-14",
      "title": "Valentine's Day",
      "description": "Optional holiday",
      "is_active": true
    }
  ]
}
```

### 2. Add Holiday (Admin)
```bash
POST /holidays
{
  "date": "2024-12-25",
  "title": "Christmas",
  "description": "Company closed",
  "is_active": true
}
```

### 3. Update Holiday (Admin)
```bash
PUT /holidays/{holiday_id}
{
  "title": "Christmas Day",
  "description": "Updated description"
}
```

### 4. Delete Holiday (Admin)
```bash
DELETE /holidays/{holiday_id}
```
- Soft delete (sets `is_active = false`)

## Database Model

```python
class Holiday(Base):
    id: int
    date: datetime
    title: str
    description: Optional[str]
    is_active: bool (default: True)
    created_at: datetime
    updated_at: datetime
```

## Use Cases

- Employees cannot clock in on holidays
- Leave requests automatically exclude holidays
- Payroll calculations skip holidays
- Calendar display highlights holidays

## Related Files

- [`app/routes/holidays.py`](file:///d:/SP/HRMS/Backend/app/routes/holidays.py) - Holiday endpoints
- [`app/models.py`](file:///d:/SP/HRMS/Backend/app/models.py#L170-L186) - Holiday model
