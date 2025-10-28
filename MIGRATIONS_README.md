# HRMS Database Migrations

## 📚 Documentation Files

- **`ALEMBIC_SETUP.md`** - Complete guide for using Alembic migrations
- **`MIGRATION_FLOW.md`** - Overall migration architecture and legacy documentation
- **`MIGRATION_QUICK_REFERENCE.md`** - Quick command reference
- **`MIGRATION_FLOW_DIAGRAM.txt`** - Visual diagrams of migration flow

## 🎯 Quick Start

### 🆕 First-Time Setup (Fresh Database)

```bash
# Option 1: If database is completely empty
# 1. Create initial migration from your models
python run_alembic_migration.py revision --autogenerate -m "Initial migration"

# 2. Apply migrations to create all tables
python run_alembic_migration.py upgrade head

# 3. Check status
python run_alembic_migration.py current

# 4. Create super admin user
python create_super_admin.py

# Option 2: If database already has tables but no migration tracking
# 1. Generate a migration that reflects current state
python run_alembic_migration.py revision --autogenerate -m "Initial schema"

# 2. Mark as applied without running SQL
python run_alembic_migration.py stamp head
```

### 📝 Updating Models (After Making Changes)

```bash
# 1. Modify your models in app/models.py
#    (Add columns, new tables, modify fields, etc.)

# 2. Generate migration file (auto-detect changes)
python run_alembic_migration.py revision --autogenerate -m "Description of changes"

# 3. Review the generated migration file
#    Check: migrations/versions/xxxxx_description_of_changes.py

# 4. Apply the migration
python run_alembic_migration.py upgrade head

# 5. Verify changes
python run_alembic_migration.py current
```

### Using Legacy Script (If Needed)

```bash
# Run the old migration script
python run_migration.py
```

## 🆕 Migration System Overview

### Alembic (Current Standard)

**Advantages**:
- ✅ Version control for migrations
- ✅ Rollback support
- ✅ Migration history tracking
- ✅ Dependency management
- ✅ Auto-generate from models

**Files**:
- `migrations/env.py` - Environment configuration with async support
- `migrations/versions/` - Migration version files
- `run_alembic_migration.py` - Migration runner script
- `alembic.ini` - Alembic configuration

**Usage**:
```bash
# Create migration (auto-detect changes from models)
python run_alembic_migration.py revision --autogenerate -m "Description"

# Apply all migrations
python run_alembic_migration.py upgrade head

# Rollback one migration
python run_alembic_migration.py downgrade -1

# Show current database version
python run_alembic_migration.py current

# Show migration history
python run_alembic_migration.py history

# Show all migration heads
python run_alembic_migration.py heads
```

### Legacy Custom Script

**Advantages**:
- ✅ Idempotent (safe to re-run)
- ✅ Simple and direct
- ✅ Good for quick fixes

**Disadvantages**:
- ❌ No version control
- ❌ No rollback
- ❌ No history

**Usage**:
```bash
python run_migration.py
```

## 📖 Common Tasks

### Add New Column to Existing Table

1. Update model in `app/models.py`:
```python
class User(Base):
    # ... existing fields
    new_field = Column(String, nullable=True)
```

2. Generate migration:
```bash
python run_alembic_migration.py revision --autogenerate -m "Add new_field to users"
```

3. Review and apply:
```bash
# Review migrations/versions/[revision]_add_new_field_to_users.py
python run_alembic_migration.py upgrade head
```

### Create New Table

1. Add model in `app/models.py`:
```python
class NewTable(Base):
    __tablename__ = "new_table"
    id = Column(Integer, primary_key=True)
    # ... fields
```

2. Generate and apply:
```bash
python run_alembic_migration.py revision --autogenerate -m "Create new_table"
python run_alembic_migration.py upgrade head
```

### Check Current Database Version

```bash
python run_alembic_migration.py current
```

### View Migration History

```bash
python run_alembic_migration.py history
```

### Rollback One Migration

```bash
python run_alembic_migration.py downgrade -1
```

## 🔧 Migration Files Structure

```
Backend/
├── migrations/
│   ├── env.py                    # Environment configuration (async support)
│   ├── script.py.mako            # Migration template
│   ├── README                     # Alembic info
│   └── versions/                 # Migration version files
│       ├── abc123_initial.py     # Example migration
│       └── xyz789_add_field.py   # Example migration
├── alembic.ini                    # Alembic configuration
├── run_alembic_migration.py       # Alembic runner (recommended)
├── migrate.py                     # Simple wrapper
├── run_migration.py               # Legacy script (old)
├── ALEMBIC_SETUP.md              # Complete guide
├── MIGRATION_FLOW.md              # Architecture docs
└── MIGRATION_QUICK_REFERENCE.md   # Quick reference
```

## ⚠️ Important Notes

1. **Always review auto-generated migrations** before applying**
2. **Test migrations on development environment first**
3. **Backup production database before migrating**
4. **Check for conflicts if working in a team**

## 🚀 For New Projects

If you're starting fresh:

```bash
# 1. Create database
createdb hrms_db

# 2. Generate initial migration
python run_alembic_migration.py revision --autogenerate -m "Initial migration"

# 3. Apply migrations
python run_alembic_migration.py upgrade head

# 4. Create super admin
python create_super_admin.py
```

## 🐛 Troubleshooting

### "No such revision"
```bash
# Check current status
python run_alembic_migration.py current

# Apply pending migrations
python run_alembic_migration.py upgrade head
```

### Autogenerate not working
```bash
# Ensure models are imported in migrations/env.py
# File should have: from app.models import Base
```

### Migration conflicts
```bash
# Merge heads if needed
python run_alembic_migration.py heads
# Resolve manually and merge
```

## 📞 Need Help?

- See `ALEMBIC_SETUP.md` for detailed guide
- See `MIGRATION_FLOW.md` for architecture details
- Check Alembic documentation: https://alembic.sqlalchemy.org/

## 🚀 Complete Initial Setup

For a brand new installation:

```bash
# 1. Start PostgreSQL database (if not running)
# Using Docker:
docker-compose up -d

# 2. Run initial migration
python run_alembic_migration.py revision --autogenerate -m "Initial schema"

# 3. Apply migrations
python run_alembic_migration.py upgrade head

# 4. Verify database is set up correctly
python run_alembic_migration.py current

# 5. Create super admin user
python create_super_admin.py

# 6. Start the backend server
# Using uvicorn (development):
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using Docker:
docker-compose up
```

## 🎯 Best Practices

1. **Use Alembic for new projects** - Better version control
2. **Review migrations before applying** - Check what will change
3. **Keep migrations small** - One logical change per migration
4. **Use descriptive messages** - Clear what each migration does
5. **Test locally first** - Never apply untested migrations to production

## 📝 Migration Checklist

Before applying migrations to production:

- [ ] Tested on development environment
- [ ] Reviewed migration file for correct changes
- [ ] Database backup created
- [ ] No data conflicts expected
- [ ] Rollback plan in place
- [ ] Team notified of schema changes
- [ ] Application tested after migration


