# HRMS Database Migration Flow

## Overview

The HRMS project now uses **Alembic** for database migrations (recommended), but also provides a legacy custom migration system in `run_migration.py` for backward compatibility.

**🆕 NEW: Use Alembic for version control and rollback capabilities**  
**📜 OLD: Legacy custom script still available**

See `ALEMBIC_SETUP.md` for Alembic migration guide.  
See below for legacy migration documentation.

## Migration Systems Available

### 🆕 Alembic (Recommended)

**Files**: `migrations/`, `run_alembic_migration.py`, `migrate.py`

**Features**:
- ✅ Version control for migrations
- ✅ Rollback support
- ✅ Migration history
- ✅ Auto-generate from models
- ✅ Dependency tracking

**Usage**:
```bash
python run_alembic_migration.py upgrade head
python run_alembic_migration.py revision --autogenerate -m "Description"
```

### 📜 Legacy Custom Script

**Files**: `run_migration.py`

**Features**:
- ✅ Idempotent operations
- ✅ Safe to re-run
- ❌ No version control
- ❌ No rollback

**Usage**:
```bash
python run_migration.py
```

## Current Migration Architecture

### Components

1. **Database Configuration** (`app/database.py`)
   - Defines async SQLAlchemy engine with connection pooling
   - Configures performance optimizations (pool size, timeouts, etc.)
   - Provides database session factory

2. **Models Definition** (`app/models.py`)
   - SQLAlchemy ORM models for all tables
   - Defines relationships, indexes, and constraints
   - Used as the source of truth for schema

3. **Alembic System** (NEW)
   - `migrations/env.py` - Migration environment (async support)
   - `migrations/versions/` - Migration files
   - `run_alembic_migration.py` - Migration runner
   - Version control, rollback, and history

4. **Legacy Migration Script** (OLD)
   - `run_migration.py` - Custom migration runner
   - Idempotent operations (safe to run multiple times)
   - Creates/modifies tables, indexes, and constraints

## Current Migration Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Database Migration Flow                    │
└─────────────────────────────────────────────────────────────┘

1. MODELS DEFINITION (app/models.py)
   ↓
   - Define all SQLAlchemy models with columns, relationships
   - Define indexes using __table_args__
   - Define enums for type safety

2. MIGRATION SCRIPT (run_migration.py)
   ↓
   ├─ Import models (Base.metadata)
   ├─ Create base tables via SQLAlchemy metadata
   ├─ Apply custom modifications:
   │   ├─ Add columns (IF NOT EXISTS)
   │   ├─ Create indexes (IF NOT EXISTS)
   │   ├─ Set default values
   │   └─ Backfill NULL values
   └─ Verify all tables/columns

3. RUN MIGRATION
   ↓
   python run_migration.py
   
4. DATABASE STATE
   ↓
   - All tables created/updated
   - All indexes created
   - Schema matches models.py
```

## How Migration Works

### Step 1: Define Models
Models are defined in `app/models.py` using SQLAlchemy declarative base:

```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    # ... other columns
```

### Step 2: Custom Migration Functions
`run_migration.py` contains idempotent functions that:

- **Ensure columns exist**: `ADD COLUMN IF NOT EXISTS`
- **Create indexes**: `CREATE INDEX IF NOT EXISTS`
- **Modify column types**: Check current type before altering
- **Backfill data**: Update NULL values with defaults

**Example:**
```python
async def ensure_user_columns(conn):
    await conn.execute(text(
        """
        ALTER TABLE users 
        ADD COLUMN IF NOT EXISTS designation VARCHAR(255) NULL,
        ADD COLUMN IF NOT EXISTS joining_date DATE NULL
        """
    ))
```

### Step 3: Run Migration
Execute the migration script:

```bash
python run_migration.py
```

The script will:
1. Connect to database using `DATABASE_URL` from `.env`
2. Create base tables using SQLAlchemy `Base.metadata.create_all()`
3. Run all custom migration functions
4. Verify all tables and columns
5. Display summary

### Step 4: Verification
The script verifies:
- All required tables exist
- Key columns are present
- Indexes are created

## Migration Functions Overview

### Current Functions in `run_migration.py`

| Function | Purpose | Tables Affected |
|----------|---------|----------------|
| `ensure_user_columns()` | Add designation, joining_date, wifi_user_id | users |
| `ensure_holiday_is_active()` | Add is_active with default TRUE | holidays |
| `ensure_identity_document_columns()` | Add document fields & statuses | users |
| `ensure_leaves_total_days_numeric()` | Convert total_days to NUMERIC(4,1) | leaves |
| `create_email_settings_table()` | Create email settings table | email_settings |
| `create_email_template_table()` | Create email templates table | email_templates |
| `create_email_log_table()` | Create email logs table | email_logs |
| `create_employee_details_table()` | Create employee details table | employee_details |
| `create_employment_history_table()` | Create employment history table | employment_history |
| `create_tasks_table()` | Create tasks table | tasks |
| `create_missing_tables()` | Create base tables from models | all |

## Database Tables

The system manages these tables:

### Core Tables
- `users` - User accounts with authentication
- `leaves` - Leave requests and approvals
- `holidays` - Company holidays

### Email Management
- `email_settings` - SMTP configuration
- `email_templates` - Email templates
- `email_logs` - Email sending history

### Employee Management
- `employee_details` - Comprehensive employee information
- `employment_history` - Employment history tracking

### Task Management
- `tasks` - User task management

## How to Add New Migrations

### Option 1: Add to Custom Migration Script

1. **Update models in `app/models.py`**:
```python
class User(Base):
    # ... existing columns
    new_column = Column(String, nullable=True)  # Add your new column
```

2. **Add migration function to `run_migration.py`**:
```python
async def ensure_new_column(conn):
    print("📝 Ensuring new_column on users...")
    await conn.execute(text(
        """
        ALTER TABLE users 
        ADD COLUMN IF NOT EXISTS new_column VARCHAR(255) NULL
        """
    ))
    print("✅ New column ensured")
```

3. **Call the function in `run_migration()`**:
```python
async def run_migration():
    # ... existing code
    await ensure_new_column(conn)
    # ... rest of code
```

4. **Run the migration**:
```bash
python run_migration.py
```

### Option 2: Convert to Alembic

If you want to use Alembic for versioned migrations:

1. **Initialize Alembic**:
```bash
cd Backend
alembic init migrations
```

2. **Update `migrations/env.py`**:
```python
from app.models import Base
target_metadata = Base.metadata
```

3. **Create initial migration**:
```bash
alembic revision --autogenerate -m "Initial migration"
```

4. **Run migrations**:
```bash
alembic upgrade head
```

## Migration Best Practices

### Idempotency
All migration operations use `IF NOT EXISTS` to make them idempotent:
- Safe to run multiple times
- Won't fail if already applied
- Good for development environments

### Backward Compatibility
- Always use nullable columns for new fields
- Provide sensible defaults
- Consider data migration for required fields

### Index Management
Indexes are created using `CREATE INDEX IF NOT EXISTS`:
- Improves query performance
- Can be safely re-run
- Automatically managed by migration script

### Testing Migrations
Before running on production:

1. Test on development database
2. Verify data integrity
3. Check performance impact
4. Review indexes created

```bash
# Test migration on dev database
python run_migration.py

# Verify schema
psql -d hrms_db -c "\d users"
psql -d hrms_db -c "\di"  # List all indexes
```

## Environment Configuration

### Database URL
The migration uses `DATABASE_URL` from environment or defaults:

```bash
# .env file
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/hrms_db
```

### Running Migrations in Different Environments

**Development:**
```bash
python run_migration.py
```

**Production (with backup):**
```bash
# Backup database first
pg_dump hrms_db > backup.sql

# Run migration
python run_migration.py

# Verify
psql -d hrms_db -f verify_schema.sql
```

## Troubleshooting

### Issue: Migration Fails
**Error**: Table already exists
**Solution**: The migration uses `IF NOT EXISTS`, so this shouldn't happen. Check for typos in table names.

### Issue: Column Type Conflicts
**Error**: Cannot alter column type
**Solution**: The `ensure_leaves_total_days_numeric()` function checks current type before altering.

### Issue: Missing Relationships
**Error**: Foreign key constraint fails
**Solution**: Ensure tables are created in dependency order:
1. `users` (base table)
2. `leaves`, `employee_details` (depend on users)
3. Others as needed

## Future Improvements

### Recommended Enhancements

1. **Version Control**: Add version tracking to migrations
2. **Rollback Support**: Implement migration rollback functionality
3. **Alembic Integration**: Convert to Alembic for better version management
4. **Migration Logging**: Track which migrations have been applied
5. **Schema Diff**: Generate diff between current schema and models

## Current Limitations

- No version tracking
- No rollback mechanism
- No migration history
- Manually call migration functions
- No automated testing of migrations

## Summary

The current migration system:
- ✅ Uses custom Python script (`run_migration.py`)
- ✅ Idempotent operations (safe to rerun)
- ✅ Manages tables, columns, and indexes
- ✅ Integrates with SQLAlchemy models
- ⚠️ No version control or migration history
- ⚠️ No automatic rollback capability

**For production**: Consider migrating to Alembic for better migration management and version control.
