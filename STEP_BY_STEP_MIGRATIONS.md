# Step-by-Step Migration Commands for HRMS

## 📋 Table of Contents
1. [Scenario A: Fresh Database (No Tables Yet)](#scenario-a-fresh-database)
2. [Scenario B: Existing Database with Tables](#scenario-b-existing-database)
3. [Scenario C: Making Changes to Models](#scenario-c-making-changes-to-models)
4. [Troubleshooting Commands](#troubleshooting-commands)

---

## Scenario A: Fresh Database (No Tables Yet)

**When to use:** Starting a new project or database

### Step 1: Navigate to Backend Directory
```bash
cd Backend
```

### Step 2: Activate Virtual Environment (if using one)
```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### Step 3: Ensure Database is Running
```bash
# Check if database is accessible
# Database should be at: postgresql://postgres:dwij9143@localhost:5432/hrms_db
```

### Step 4: Create Initial Migration
```bash
python run_alembic_migration.py revision --autogenerate -m "Initial migration"
```

**Expected output:**
- Creates a new file in `migrations/versions/` with timestamp and description
- Example: `migrations/versions/abc123_initial_migration.py`

### Step 5: Review the Generated Migration (Optional but Recommended)
```bash
# Open and check the generated file
# File location: migrations/versions/xxxxx_initial_migration.py
```

### Step 6: Apply Migration to Database
```bash
python run_alembic_migration.py upgrade head
```

**Expected output:**
- Shows migration being applied
- Creates all tables in database

### Step 7: Verify Migration
```bash
python run_alembic_migration.py current
```

**Expected output:**
- Shows current database revision ID
- Example: `abc123 (head)`

### Step 8: Create Super Admin User
```bash
python create_super_admin.py
```

### Step 9: (Optional) Check Migration History
```bash
python run_alembic_migration.py history
```

**You're done! Database is ready for your application.**

---

## Scenario B: Existing Database with Tables

**When to use:** Database already has tables but no Alembic tracking

### Step 1: Navigate to Backend Directory
```bash
cd Backend
```

### Step 2: Activate Virtual Environment (if using one)
```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### Step 3: Create Initial Migration from Existing Schema
```bash
python run_alembic_migration.py revision --autogenerate -m "Initial schema"
```

**This generates a migration that captures your current database state**

### Step 4: Review the Generated Migration (Important!)
```bash
# Check migrations/versions/xxxxx_initial_schema.py
# It should be mostly empty or show "pass" (no changes)
```

### Step 5: Mark Database as Up-to-Date (Without Running Changes)
```bash
python run_alembic_migration.py stamp head
```

**This tells Alembic that your database is already at this revision**

### Step 6: Verify Current Version
```bash
python run_alembic_migration.py current
```

**You're done! Your existing database is now tracked by Alembic.**

---

## Scenario C: Making Changes to Models

**When to use:** After editing models in `app/models.py`

### Step 1: Make Your Model Changes
```bash
# Edit app/models.py
# Example: Add a new field, modify existing field, add new table, etc.
```

### Step 2: Create Migration with Auto-Detection
```bash
python run_alembic_migration.py revision --autogenerate -m "Add description field to users"
```

**Replace "Add description field to users" with your actual change description**

### Step 3: Review the Generated Migration (IMPORTANT!)
```bash
# Always review migrations/versions/xxxxx_your_description.py
# Check:
# - Are the changes correct?
# - Are there any unexpected changes?
# - Any data loss concerns?
```

### Step 4: Apply the Migration
```bash
python run_alembic_migration.py upgrade head
```

### Step 5: Verify Changes
```bash
python run_alembic_migration.py current
```

### Step 6: (Optional) Check What Was Applied
```bash
python run_alembic_migration.py history
```

**You're done! Your database is updated with model changes.**

---

## Troubleshooting Commands

### Check Current Database Version
```bash
python run_alembic_migration.py current
```

### Show All Migration History
```bash
python run_alembic_migration.py history
```

### Show All Migration Heads
```bash
python run_alembic_migration.py heads
```

### Rollback One Migration
```bash
python run_alembic_migration.py downgrade -1
```

### Rollback Multiple Migrations
```bash
# Rollback 2 migrations
python run_alembic_migration.py downgrade -2

# Rollback to specific revision
python run_alembic_migration.py downgrade abc123
```

### Rollback All Migrations
```bash
python run_alembic_migration.py downgrade base
```

### Show Specific Migration Details
```bash
python run_alembic_migration.py show abc123
```

### Check for Unapplied Migrations
```bash
python run_alembic_migration.py heads
python run_alembic_migration.py current

# If they differ, run:
python run_alembic_migration.py upgrade head
```

### Merge Migration Heads (When Working in Teams)
```bash
# If you have multiple heads (usually from team collaboration)
python run_alembic_migration.py heads

# Merge them
python run_alembic_migration.py merge -m "Merge migration heads" abc123 def456

# Then apply
python run_alembic_migration.py upgrade head
```

---

## Quick Command Reference

| Task | Command |
|------|---------|
| Create migration | `python run_alembic_migration.py revision --autogenerate -m "Description"` |
| Apply migrations | `python run_alembic_migration.py upgrade head` |
| Show current version | `python run_alembic_migration.py current` |
| Show history | `python run_alembic_migration.py history` |
| Rollback one migration | `python run_alembic_migration.py downgrade -1` |
| Mark as applied (stamp) | `python run_alembic_migration.py stamp head` |
| Show heads | `python run_alembic_migration.py heads` |

---

## Important Notes

⚠️ **Always Review Migrations Before Applying**
- Generated migrations might need manual adjustments
- Check for data loss, column renames, etc.

⚠️ **Backup Production Database**
- Always backup before applying migrations to production
- Test on development environment first

⚠️ **Don't Edit Applied Migrations**
- Once a migration is applied, never edit it
- Create a new migration to fix issues

⚠️ **Team Collaboration**
- Pull latest migrations before creating new ones
- Run `python run_alembic_migration.py upgrade head` after pulling

---

## Common Issues and Solutions

### Issue: "Can't locate revision"
**Solution:** Run `python run_alembic_migration.py upgrade head`

### Issue: "Multiple heads detected"
**Solution:** Run `python run_alembic_migration.py merge` and then upgrade

### Issue: "Target database is not up to date"
**Solution:** Apply pending migrations first, then try again

### Issue: Autogenerate not detecting changes
**Solution:** 
1. Check `migrations/env.py` has `from app.models import Base`
2. Check `target_metadata = Base.metadata`
3. Restart and try again

---

**Need more help?** Check these files:
- `MIGRATIONS_README.md` - Complete guide
- `COMMAND.md` - Quick reference
- `MIGRATION_SETUP_COMPLETE.md` - Setup summary

