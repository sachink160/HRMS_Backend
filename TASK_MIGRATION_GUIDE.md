# Task Model Migration Update

## Overview
The `run_migration.py` file has been updated to include the Task model creation and database migration for the Task Management API.

## Changes Made

### 1. Added Task Table Creation Function
```python
async def create_tasks_table(conn):
    """Creates the tasks table with all necessary columns and indexes"""
```

**Table Structure:**
- `id` - Primary key (SERIAL)
- `user_id` - Foreign key to users table
- `name` - Task name (VARCHAR, NOT NULL)
- `description` - Task description (TEXT)
- `status` - Task status (VARCHAR, DEFAULT 'pending')
- `due_date` - Due date (TIMESTAMP WITH TIME ZONE)
- `completed_at` - Completion timestamp (TIMESTAMP WITH TIME ZONE)
- `priority` - Task priority (VARCHAR, DEFAULT 'medium')
- `category` - Task category (VARCHAR)
- `is_active` - Soft delete flag (BOOLEAN, DEFAULT TRUE)
- `created_at` - Creation timestamp (TIMESTAMP WITH TIME ZONE)
- `updated_at` - Last update timestamp (TIMESTAMP WITH TIME ZONE)

### 2. Database Indexes Created
The migration creates the following indexes for optimal performance:

- `idx_task_user_id` - For user-specific queries
- `idx_task_status` - For status filtering
- `idx_task_priority` - For priority filtering
- `idx_task_category` - For category filtering
- `idx_task_due_date` - For due date queries
- `idx_task_active` - For active/inactive filtering
- `idx_task_created_at` - For chronological ordering
- `idx_task_user_status` - Composite index for user + status queries
- `idx_task_user_created` - Composite index for user + creation date queries

### 3. Updated Migration Flow
The migration now includes:
1. **Base table creation** (users, leaves, holidays)
2. **Email management tables** (email_settings, email_templates, email_logs)
3. **Employee management tables** (employee_details, employment_history)
4. **Task management table** (tasks) ← **NEW**
5. **Verification** of all tables and columns

### 4. Updated Verification
The verification function now checks for:
- Tasks table existence
- Key columns in tasks table
- Proper foreign key relationships

### 5. Manual Table Creation Fallback
Added tasks table creation to the manual fallback method in case SQLAlchemy metadata creation fails.

## How to Run the Migration

### Option 1: Run the Updated Migration Script
```bash
cd Backend
python run_migration.py
```

### Option 2: Test the Migration First
```bash
cd Backend
python test_task_migration.py
```

## Expected Output
When running the migration, you should see:
```
📝 Creating tasks table...
✅ Tasks table created
🔍 Verifying all tables and key columns...
📋 Existing tables:
   ✅ users
   ✅ leaves
   ✅ holidays
   ✅ email_settings
   ✅ email_templates
   ✅ email_logs
   ✅ employee_details
   ✅ employment_history
   ✅ tasks
🔍 Key columns verified:
   - tasks.user_id: integer
```

## Migration Features

### ✅ Idempotent Operations
- All operations use `IF NOT EXISTS` clauses
- Safe to run multiple times
- Won't duplicate data or structures

### ✅ Performance Optimized
- Comprehensive indexing strategy
- Optimized for common query patterns
- Composite indexes for complex queries

### ✅ Data Integrity
- Foreign key constraints to users table
- Proper data types and constraints
- Soft delete support with `is_active` flag

### ✅ Backward Compatible
- Doesn't affect existing tables
- Maintains all existing functionality
- Adds new features without breaking changes

## Task Status Values
The migration creates the tasks table with support for these status values:
- `pending` - Task is waiting to be started
- `in_progress` - Task is currently being worked on
- `completed` - Task has been finished
- `cancelled` - Task has been cancelled

## Priority Levels
- `low` - Low priority tasks
- `medium` - Medium priority tasks (default)
- `high` - High priority tasks
- `urgent` - Urgent tasks requiring immediate attention

## Post-Migration Steps

1. **Verify Migration Success**
   ```bash
   python test_task_migration.py
   ```

2. **Start the Backend Server**
   ```bash
   uvicorn app.main:app --reload
   ```

3. **Test Task API Endpoints**
   ```bash
   python test_task_api.py
   ```

4. **Check API Documentation**
   - Visit `http://localhost:8000/docs` for interactive API documentation
   - Review `TASK_API_DOCUMENTATION.md` for detailed usage guide

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Check DATABASE_URL in .env file
   - Ensure PostgreSQL is running
   - Verify database credentials

2. **Permission Errors**
   - Ensure database user has CREATE TABLE permissions
   - Check if database exists and is accessible

3. **Migration Fails**
   - Check logs for specific error messages
   - Verify all dependencies are installed
   - Try running the test script first

### Rollback (if needed)
If you need to rollback the tasks table:
```sql
DROP TABLE IF EXISTS tasks CASCADE;
```

## Next Steps

After successful migration:

1. **Frontend Integration** - Update frontend to use Task API endpoints
2. **User Training** - Train users on task management features
3. **Monitoring** - Set up monitoring for task-related metrics
4. **Enhancements** - Consider adding task assignments, subtasks, etc.

## Support

For issues or questions:
1. Check the migration logs
2. Review the test script output
3. Verify database connectivity
4. Check API endpoint responses

The Task Management system is now ready for use! 🎉
