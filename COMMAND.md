# Quick Command Reference for HRMS Migrations

## First-time setup (fresh database)
# Step 1: Create initial migration from models
python run_alembic_migration.py revision --autogenerate -m "Initial migration"

# Step 2: Apply migration
python run_alembic_migration.py upgrade head

# Step 3: Create super admin
python create_super_admin.py

# Step 4: Verify database version
python run_alembic_migration.py current


## If database already has tables (no migrations yet)
# Generate migration that reflects current state
python run_alembic_migration.py revision --autogenerate -m "Initial schema"

# Stamp database as up-to-date (apply without SQL changes)
python run_alembic_migration.py stamp head


## After updating models (add/edit tables/columns)
# Step 1: Edit app/models.py (add fields, tables, etc.)
# Step 2: Generate migration (auto-detect changes)
python run_alembic_migration.py revision --autogenerate -m "Description of changes"

# Step 3: Review generated file in migrations/versions/
# Step 4: Apply migration
python run_alembic_migration.py upgrade head


## Useful commands
# Show current database version
python run_alembic_migration.py current

# Show migration history
python run_alembic_migration.py history

# Rollback one migration
python run_alembic_migration.py downgrade -1

# Rollback to specific revision
python run_alembic_migration.py downgrade <revision_id>

# Show migration heads
python run_alembic_migration.py heads

