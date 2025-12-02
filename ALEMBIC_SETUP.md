# Alembic Migration Setup Guide

## Overview

The HRMS project now uses **Alembic** for database migrations. This provides better version control, rollback capabilities, and migration history tracking.

alembic revision --autogenerate -m "Initial migration"
alembic upgrade head

## New Migration Structure

```
Backend/
├── alembic.ini              # Alembic configuration
├── migrations/               # Migration directory
│   ├── env.py               # Environment configuration (async support)
│   ├── script.py.mako       # Migration template
│   ├── README               # Alembic info
│   └── versions/            # Migration versions (created by Alembic)
├── run_alembic_migration.py # Alembic migration runner
├── migrate.py               # Simple migration wrapper
└── run_migration.py         # Legacy migration script (backup)
```

## Quick Start

### 1. Initialize Database (First Time)

```bash
# Create initial migration from models
python run_alembic_migration.py revision --autogenerate -m "Initial migration"

# Apply migrations
python run_alembic_migration.py upgrade head
```

### 2. Check Migration Status

```bash
# Show current version
python run_alembic_migration.py current

# Show migration history
python run_alembic_migration.py history

# Show all heads
python run_alembic_migration.py heads
```

### 3. Create New Migration

```bash
# Auto-generate from model changes
python run_alembic_migration.py revision --autogenerate -m "Add new column"

# Or create empty migration
python run_alembic_migration.py revision -m "Manual migration"
```

### 4. Apply Migrations

```bash
# Apply all pending migrations
python run_alembic_migration.py upgrade head

# Apply to specific revision
python run_alembic_migration.py upgrade <revision_id>
```

### 5. Rollback Migrations

```bash
# Rollback one migration
python run_alembic_migration.py downgrade -1

# Rollback to specific revision
python run_alembic_migration.py downgrade <revision_id>
```

## Commands Reference

### Migration Commands

| Command | Description |
|---------|-------------|
| `upgrade head` | Apply all pending migrations to the latest version |
| `upgrade <revision>` | Upgrade to specific revision |
| `downgrade -1` | Rollback one migration |
| `downgrade <revision>` | Rollback to specific revision |
| `current` | Show current database version |
| `history` | Show migration history |
| `heads` | Show current migration heads |
| `revision -m MESSAGE` | Create new migration manually |
| `revision --autogenerate -m MESSAGE` | Auto-generate migration from models |
| `show <revision>` | Show migration details |
| `stamp <revision>` | Stamp database without running migration |

## Workflow

### Adding New Model Fields

1. **Update the model** in `app/models.py`:
   ```python
   class User(Base):
       # ... existing fields
       new_field = Column(String, nullable=True)
   ```

2. **Generate migration**:
   ```bash
   python run_alembic_migration.py revision --autogenerate -m "Add new_field to users"
   ```

3. **Review the generated migration** in `migrations/versions/`:
   ```python
   # Review the upgrade/downgrade functions
   ```

4. **Apply the migration**:
   ```bash
   python run_alembic_migration.py upgrade head
   ```

### Adding New Tables

1. **Create model** in `app/models.py`:
   ```python
   class NewTable(Base):
       __tablename__ = "new_table"
       id = Column(Integer, primary_key=True)
       # ... fields
   ```

2. **Generate migration**:
   ```bash
   python run_alembic_migration.py revision --autogenerate -m "Create new_table"
   ```

3. **Apply migration**:
   ```bash
   python run_alembic_migration.py upgrade head
   ```

## Migration Files Structure

Each migration file in `migrations/versions/` contains:

```python
"""Add new field

Revision ID: abc123
Revises: xyz789
Create Date: 2024-01-15 10:30:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'abc123'
down_revision = 'xyz789'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply this migration."""
    # Add new column
    op.add_column('users', sa.Column('new_field', sa.String(), nullable=True))


def downgrade() -> None:
    """Rollback this migration."""
    # Remove the column
    op.drop_column('users', 'new_field')
```

## Database URL Configuration

The migration uses the same database URL as the application:

```env
# .env file
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/hrms_db
```

You can override it in `alembic.ini` if needed.

## Troubleshooting

### Issue: "No such revision"

**Error**: `alembic.util.exc.CommandError: Target database is not up to date`

**Solution**: Check current version and apply migrations:
```bash
python run_alembic_migration.py current
python run_alembic_migration.py upgrade head
```

### Issue: Autogenerate not detecting changes

**Possible causes**:
1. Model changes not imported in `migrations/env.py`
2. Database already has the changes manually applied

**Solution**: 
1. Ensure all models are imported in `env.py`:
   ```python
   from app.models import Base
   ```
2. Use `--sql` flag to preview changes:
   ```bash
   alembic revision --autogenerate -m "Test" --sql
   ```

### Issue: Migration conflicts

**Error**: Multiple heads detected

**Solution**: Merge migrations:
```bash
python run_alembic_migration.py merge heads -m "Merge branches"
python run_alembic_migration.py upgrade head
```

### Issue: Downgrade fails

**Error**: Cannot downgrade due to data constraints

**Solution**:
1. Review migration downgrade function
2. Handle data migration manually
3. Or manually adjust the downgrade logic

## Best Practices

### 1. Always Review Auto-Generated Migrations

```bash
# Generate migration
python run_alembic_migration.py revision --autogenerate -m "Add field"

# Review the file in migrations/versions/
# Edit if needed

# Then apply
python run_alembic_migration.py upgrade head
```

### 2. Use Descriptive Messages

```bash
# Good
python run_alembic_migration.py revision --autogenerate -m "Add email_verified field to users"

# Bad
python run_alembic_migration.py revision --autogenerate -m "Update"
```

### 3. Test Migrations Locally First

```bash
# Test on development
python run_alembic_migration.py upgrade head

# Then on staging
# Finally on production
```

### 4. Backup Before Migrating Production

```bash
# Backup database
pg_dump hrms_db > backup_$(date +%Y%m%d).sql

# Run migration
python run_alembic_migration.py upgrade head

# Verify
python run_alembic_migration.py current
```

### 5. Keep Migrations Small and Focused

Create separate migrations for unrelated changes:
- One migration for adding columns
- One migration for adding indexes
- One migration for data updates

## Advanced Usage

### Custom Data Migrations

For data changes that can't be auto-generated:

```python
def upgrade() -> None:
    # Run custom SQL
    op.execute("UPDATE users SET status = 'active' WHERE status IS NULL")
    
    # Or use connection for complex operations
    bind = op.get_bind()
    bind.execute("UPDATE users SET ...")

def downgrade() -> None:
    op.execute("UPDATE users SET status = NULL WHERE status = 'active'")
```

### Conditional Migrations

Check current schema before making changes:

```python
def upgrade() -> None:
    inspector = op.inspect(op.get_bind())
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'new_column' not in columns:
        op.add_column('users', sa.Column('new_column', sa.String()))
```

## Migration from Old System

If you have an existing database from the old `run_migration.py`:

### Option 1: Create Initial Migration from Current Database

```bash
# Stamp the database with current state
python run_alembic_migration.py stamp head

# Or create baseline migration
python run_alembic_migration.py revision -m "Baseline from existing database"
```

### Option 2: Fresh Start

```bash
# Backup data
pg_dump hrms_db > backup.sql

# Drop and recreate database
dropdb hrms_db
createdb hrms_db

# Apply all migrations from scratch
python run_alembic_migration.py upgrade head

# Restore data (adjust schema if needed)
psql hrms_db < backup.sql
```

## Comparison: Old vs New

| Feature | Old System | Alembic |
|---------|-----------|---------|
| Version Control | ❌ No | ✅ Yes |
| Rollback | ❌ No | ✅ Yes |
| Migration History | ❌ No | ✅ Yes |
| Auto-generate | ✅ Yes | ✅ Yes |
| Manual Migrations | ✅ Yes | ✅ Yes |
| Dependencies | ⚠️ Manual | ✅ Automatic |

## Next Steps

1. Review the generated migration files in `migrations/versions/`
2. Apply migrations to your database
3. Update deployment scripts to use Alembic
4. Add migration checks to CI/CD pipeline

## References

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- See `MIGRATION_FLOW.md` for the old system documentation


