# Monthly Leave System Update - Complete ✅

## Summary

The leave calculation system has been updated from annual allocation to **monthly accrual** (1 leave per month based on months worked).

## What Changed

### ✅ New Leave Calculation Logic

**Previous:** Fixed 18 leaves per year for everyone  
**Now:** Dynamic leaves based on months worked (1 leave per month)

### Example Calculation

**Employee joined:** January 2024 (10 months ago)  
**Available leaves:** 10 leaves (1 per month)  
**Approved leaves taken:** 4 leaves  
**Remaining leaves:** 10 - 4 = **6 leaves**  
**Total leaves taken:** 4 (approved) + 0 (pending) + 0 (rejected) = **4 leaves**

### Another Example

**Employee joined:** March 2024 (8 months ago)  
**Available leaves:** 8 leaves (1 per month)  
**Approved leaves taken:** 8 leaves  
**Remaining leaves:** 8 - 8 = **0 leaves**  
**Total leaves taken:** 8 (approved) + 1 (pending) + 0 (rejected) = **9 leaves**

## How It Works

### Leave Allocation Formula

```python
# Calculate months from joining date to current date
months_worked = (current_year - joining_year) * 12 + (current_month - joining_month)
if current_day >= joining_day:
    months_worked += 1

# Available leaves = 1 per month worked
allocated_leaves = months_worked

# Remaining leaves = Available - Approved
remaining_leaves = allocated_leaves - approved_leaves
```

### Example Scenarios

| Joining Date | Current Date | Months Worked | Allocated | Approved | Remaining |
|--------------|--------------|--------------|-----------|----------|-----------|
| Jan 1, 2024  | Oct 1, 2024  | 9            | 9         | 3        | 6         |
| Jan 15, 2024 | Oct 20, 2024 | 10           | 10        | 4        | 6         |
| Mar 1, 2024  | Oct 15, 2024 | 8            | 8         | 8        | 0         |
| Jun 2024     | Oct 2024     | 5            | 5         | 2        | 3         |

## Implementation Details

### Backend Changes (`app/routes/admin.py`)

**Lines 1368-1416:**

1. **Get current date** for calculations
2. **Calculate months worked** from joining date
3. **Allocate 1 leave per month** worked
4. **Calculate remaining leaves** (allocated - approved)
5. **Calculate total leaves taken** (all statuses combined)

### Frontend Changes (`src/pages/admin/Reports.tsx`)

- Updated table header: "Total Leaves Taken" (replaces "Total Applied")
- Now shows accurate count of all leaves taken across all statuses
- Breakdown still shows: "X approved, Y pending, Z rejected"

## Features

### ✅ Monthly Accrual System

- **1 leave per month** of work
- Calculated from joining date
- Automatic adjustment as months pass
- No fixed annual allocation

### ✅ Accurate Reporting

- **Total Leaves Taken:** Sum of approved + pending + rejected
- **Remaining Leaves:** Allocated (months worked) - Approved
- **Real-time calculation** based on current date

### ✅ User-Friendly Display

- Color-coded remaining leave balance
- Clear breakdown by status
- Summary cards at top
- Dark mode support

## Calculation Logic

### Scenario 1: New Employee
- Joined: Today (1 month)
- Allocated: 1 leave
- Approved: 0
- Remaining: 1 leave

### Scenario 2: Experienced Employee  
- Joined: 10 months ago
- Allocated: 10 leaves
- Approved: 4 leaves
- Pending: 1 leave
- Remaining: 6 leaves
- Total Taken: 5 leaves

### Scenario 3: Used All Leaves
- Joined: 8 months ago
- Allocated: 8 leaves
- Approved: 8 leaves
- Pending: 1 leave
- Remaining: 0 leaves
- Total Taken: 9 leaves

## Benefits

✅ **Fair allocation** - Employees earn leaves as they work  
✅ **No waste** - New employees start with earned leaves  
✅ **Clear tracking** - See months worked vs leaves taken  
✅ **Automatic updates** - Calculates based on current date  
✅ **Accurate remaining** - Reflects actual available balance  

## Configuration

### Change Monthly Accrual Rate

If you want to change from 1 leave per month to another rate:

Edit `Backend/app/routes/admin.py` line 1393:

```python
# Current: 1 leave per month
allocated_leaves = total_months

# Change to 2 leaves per month
allocated_leaves = total_months * 2

# Change to 1.5 leaves per month (requires float calculation)
allocated_leaves = int(total_months * 1.5)
```

### Change to Quarterly Accrual

```python
# 3 leaves per quarter
quarters = total_months // 3
allocated_leaves = quarters * 3
```

## Testing

To test the new system:

1. **Check employee joining dates** are set correctly
2. **Create leave applications** for employees
3. **View Reports page** to see calculated leaves
4. **Verify remaining leaves** matches expected calculation

### Expected Behavior

- Employee with 10 months worked should have 10 allocated leaves
- If they took 4 approved leaves, remaining should be 6
- Total leaves taken should show 4 (if no pending/rejected)

## Database Requirements

Ensure all employees have a **joining_date** set:

```sql
UPDATE users SET joining_date = '2024-01-01' WHERE joining_date IS NULL;
```

## Migration from Annual to Monthly

If you have existing data with annual allocation:

1. **No migration needed** - System calculates from joining date
2. **Existing leaves** are counted as taken
3. **Remaining leaves** automatically recalculated
4. **All data preserved**

## Examples

### Example 1: Employee Taking 4 Leaves
```
Joining Date: January 2024 (10 months ago)
Allocated: 10 leaves
Approved: 4 leaves  
Remaining: 6 leaves
Total Taken: 4 leaves (4 approved + 0 pending + 0 rejected)
```

### Example 2: Employee Using All Leaves  
```
Joining Date: March 2024 (8 months ago)
Allocated: 8 leaves
Approved: 8 leaves
Remaining: 0 leaves
Total Taken: 8 leaves (8 approved + 0 pending + 0 rejected)
```

### Example 3: Multiple Status Leaves
```
Joining Date: June 2024 (5 months ago)
Allocated: 5 leaves
Approved: 3 leaves
Pending: 1 leave
Rejected: 1 leave
Remaining: 2 leaves
Total Taken: 5 leaves (3 approved + 1 pending + 1 rejected)
```

## Files Modified

- `Backend/app/routes/admin.py` - Updated leave calculation logic
- `Frontend/src/pages/admin/Reports.tsx` - Updated display labels

---

**Monthly leave accrual system is now active!** 🎉

Employees earn **1 leave per month** of work, giving fair allocation based on tenure.

