# Why Darshan Has 22 Days of Leave?

## The Answer

**Darshan has 22 allocated leaves because he joined 22 months ago.**

## How It Works

### Monthly Leave Accrual System

1. **Each month worked = 1 leave allocated**
2. **Allocated leaves = Months since joining date**
3. **Remaining leaves = Allocated leaves - Approved leaves**

## Darshan's Calculation

### Scenario:
- **Joining Date:** ~22 months ago (approximately January 2023)
- **Current Date:** October 2024
- **Months Worked:** 22 months
- **Allocated Leaves:** 22 (1 per month × 22 months)
- **Approved Leaves:** 0
- **Remaining Leaves:** 22 - 0 = 22 days

## Why Different Employees Have Different Leaves?

### Example Comparison:

| Employee | Joining Date | Months Worked | Allocated | Approved | Remaining |
|----------|--------------|--------------|-----------|----------|----------|
| Darshan | Jan 2023 (22 months ago) | 22 | 22 | 0 | 22 |
| Sachin | Oct 2024 (this month) | 1 | 1 | 0 | 1 |
| Yash | Oct 2024 (this month) | 1 | 1 | 0 | 1 |

## The Logic Explained

### If Darshan Takes 4 Approved Leaves:

- **Allocated:** 22 leaves
- **Approved:** 4 leaves (after taking 4)
- **Remaining:** 22 - 4 = **18 leaves**
- **Total Taken:** 4 leaves

### If He Takes More Leaves:

- **Approved:** 10 leaves
- **Remaining:** 22 - 10 = **12 leaves**
- **Total Taken:** 10 leaves

## Formula

```python
# Calculate months worked
years_diff = current_date.year - joining_date.year
months_diff = current_date.month - joining_date.month
total_months = years_diff * 12 + months_diff

# If past the joining day in current month, add 1
if current_date.day >= joining_date.day:
    total_months += 1

# Allocated leaves = months worked
allocated_leaves = total_months

# Remaining = Allocated - Approved
remaining_leaves = allocated_leaves - approved_leaves
```

## Why This System?

✅ **Fair:** Employees earn leaves as they work  
✅ **Automatic:** No manual calculation needed  
✅ **Accurate:** Based on actual months worked  
✅ **Transparent:** Easy to understand  

## Common Scenarios

### 1. New Employee (1 month)
- Allocated: 1 leave
- Approved: 0
- Remaining: 1

### 2. 6 Month Employee
- Allocated: 6 leaves
- Approved: 2
- Remaining: 4

### 3. 1 Year Employee
- Allocated: 12 leaves
- Approved: 3
- Remaining: 9

### 4. 2 Year Employee (Like Darshan)
- Allocated: 24 leaves (or 22 if joined partway through)
- Approved: 0
- Remaining: 22

## Is 22 Days Correct for Darshan?

**YES!** If Darshan joined approximately 22 months ago, he has:
- **Earned:** 22 leaves (1 per month)
- **Taken:** 0 approved leaves
- **Remaining:** 22 leaves

This is **correct** behavior for the monthly accrual system.

## What If You Want to Change the Allocation?

You can modify the rate in `Backend/app/routes/admin.py`:

```python
# Current: 1 leave per month
allocated_leaves = total_months

# Change to 1.5 leaves per month
allocated_leaves = int(total_months * 1.5)

# Change to 2 leaves per month
allocated_leaves = total_months * 2
```

## Summary

Darshan has 22 days because he's been working for 22 months and hasn't taken any approved leave yet. The system is working correctly! 🎉

