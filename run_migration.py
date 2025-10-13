"""
Comprehensive migration script to align the database with current models and flows.

Actions performed (idempotent):
- Ensure `users.designation`, `users.joining_date`, `users.wifi_user_id` (+ index)
- Ensure `holidays.is_active` with TRUE default and backfill NULLs
- Ensure identity document columns on `users`
- Ensure `leaves.total_days` exists and is NUMERIC(4,1) for half-days
- Create email-related tables: `email_settings`, `email_templates`, `email_logs`
- Create employee management tables: `employee_details`, `employment_history`
- Create all necessary indexes and constraints
- Create any missing tables/indexes from SQLAlchemy models (`Base.metadata.create_all`)
"""

import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

try:
    # Prefer app-provided DATABASE_URL if available
    from app.database import DATABASE_URL as APP_DATABASE_URL
except Exception:
    APP_DATABASE_URL = None

load_dotenv()

def get_database_url() -> str:
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url
    if APP_DATABASE_URL:
        return APP_DATABASE_URL
    return "postgresql+asyncpg://postgres:dwij9143@localhost:5432/hrms_db"


async def ensure_user_columns(conn):
    print("📝 Ensuring user columns (designation, joining_date, wifi_user_id)...")
    await conn.execute(text(
        """
        ALTER TABLE users 
        ADD COLUMN IF NOT EXISTS designation VARCHAR(255) NULL,
        ADD COLUMN IF NOT EXISTS joining_date DATE NULL,
        ADD COLUMN IF NOT EXISTS wifi_user_id VARCHAR(255) NULL
        """
    ))
    
    # Create all user table indexes
    user_indexes = [
        "CREATE INDEX IF NOT EXISTS ix_users_wifi_user_id ON users (wifi_user_id)",
        "CREATE INDEX IF NOT EXISTS idx_user_role ON users (role)",
        "CREATE INDEX IF NOT EXISTS idx_user_active ON users (is_active)",
        "CREATE INDEX IF NOT EXISTS idx_user_created_at ON users (created_at)",
        "CREATE INDEX IF NOT EXISTS idx_user_role_active ON users (role, is_active)"
    ]
    for index_sql in user_indexes:
        await conn.execute(text(index_sql))
    print("✅ User columns and indexes ensured")


async def ensure_holiday_is_active(conn):
    print("📝 Ensuring holidays.is_active column...")
    await conn.execute(text(
        """
        ALTER TABLE holidays
        ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE
        """
    ))
    await conn.execute(text(
        """
        UPDATE holidays SET is_active = TRUE WHERE is_active IS NULL
        """
    ))
    
    # Create holiday table indexes
    holiday_indexes = [
        "CREATE INDEX IF NOT EXISTS idx_holiday_date ON holidays (date)",
        "CREATE INDEX IF NOT EXISTS idx_holiday_active ON holidays (is_active)",
        "CREATE INDEX IF NOT EXISTS idx_holiday_date_active ON holidays (date, is_active)"
    ]
    for index_sql in holiday_indexes:
        await conn.execute(text(index_sql))
    print("✅ Holiday is_active ensured and backfilled with indexes")


async def ensure_identity_document_columns(conn):
    print("📝 Ensuring identity document columns on users...")
    await conn.execute(text(
        """
        ALTER TABLE users 
        ADD COLUMN IF NOT EXISTS profile_image VARCHAR,
        ADD COLUMN IF NOT EXISTS aadhaar_front VARCHAR,
        ADD COLUMN IF NOT EXISTS aadhaar_back VARCHAR,
        ADD COLUMN IF NOT EXISTS pan_image VARCHAR,
        ADD COLUMN IF NOT EXISTS profile_image_status VARCHAR,
        ADD COLUMN IF NOT EXISTS aadhaar_front_status VARCHAR,
        ADD COLUMN IF NOT EXISTS aadhaar_back_status VARCHAR,
        ADD COLUMN IF NOT EXISTS pan_image_status VARCHAR
        """
    ))
    print("✅ Identity document columns ensured")


async def ensure_leaves_total_days_numeric(conn):
    print("📝 Ensuring leaves.total_days supports half-days (NUMERIC(4,1))...")
    # Check current column status
    result = await conn.execute(text(
        """
        SELECT data_type 
        FROM information_schema.columns 
        WHERE table_name = 'leaves' AND column_name = 'total_days'
        """
    ))
    row = result.fetchone()
    if row is None:
        # Add as NUMERIC(4,1)
        await conn.execute(text(
            """
            ALTER TABLE leaves 
            ADD COLUMN total_days NUMERIC(4,1) NOT NULL DEFAULT 1.0
            """
        ))
        await conn.execute(text(
            """
            ALTER TABLE leaves 
            ALTER COLUMN total_days DROP DEFAULT
            """
        ))
        print("✅ Added total_days as NUMERIC(4,1)")
        return

    data_type = row[0]
    if data_type != 'numeric':
        await conn.execute(text(
            """
            ALTER TABLE leaves 
            ALTER COLUMN total_days TYPE NUMERIC(4,1)
            """
        ))
        print("✅ Converted total_days to NUMERIC(4,1)")
    else:
        print("ℹ️ total_days already numeric; no changes needed")
    
    # Create leaves table indexes
    leaves_indexes = [
        "CREATE INDEX IF NOT EXISTS idx_leave_user_id ON leaves (user_id)",
        "CREATE INDEX IF NOT EXISTS idx_leave_status ON leaves (status)",
        "CREATE INDEX IF NOT EXISTS idx_leave_dates ON leaves (start_date, end_date)",
        "CREATE INDEX IF NOT EXISTS idx_leave_user_status ON leaves (user_id, status)",
        "CREATE INDEX IF NOT EXISTS idx_leave_created_at ON leaves (created_at)",
        "CREATE INDEX IF NOT EXISTS idx_leave_user_created ON leaves (user_id, created_at)"
    ]
    for index_sql in leaves_indexes:
        await conn.execute(text(index_sql))
    print("✅ Leaves table indexes ensured")


async def create_email_settings_table(conn):
    print("📝 Creating email_settings table...")
    await conn.execute(text(
        """
        CREATE TABLE IF NOT EXISTS email_settings (
            id SERIAL PRIMARY KEY,
            smtp_server VARCHAR NOT NULL,
            smtp_port INTEGER NOT NULL,
            smtp_username VARCHAR NOT NULL,
            smtp_password VARCHAR NOT NULL,
            smtp_use_tls BOOLEAN DEFAULT TRUE,
            smtp_use_ssl BOOLEAN DEFAULT FALSE,
            from_email VARCHAR NOT NULL,
            from_name VARCHAR NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE
        )
        """
    ))
    await conn.execute(text(
        """
        CREATE INDEX IF NOT EXISTS idx_email_settings_active ON email_settings (is_active)
        """
    ))
    print("✅ Email settings table created")


async def create_email_template_table(conn):
    print("📝 Creating email_templates table...")
    await conn.execute(text(
        """
        CREATE TABLE IF NOT EXISTS email_templates (
            id SERIAL PRIMARY KEY,
            name VARCHAR NOT NULL UNIQUE,
            subject VARCHAR NOT NULL,
            body TEXT NOT NULL,
            template_type VARCHAR NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE
        )
        """
    ))
    await conn.execute(text(
        """
        CREATE INDEX IF NOT EXISTS idx_email_template_type ON email_templates (template_type)
        """
    ))
    await conn.execute(text(
        """
        CREATE INDEX IF NOT EXISTS idx_email_template_active ON email_templates (is_active)
        """
    ))
    print("✅ Email templates table created")


async def create_email_log_table(conn):
    print("📝 Creating email_logs table...")
    await conn.execute(text(
        """
        CREATE TABLE IF NOT EXISTS email_logs (
            id SERIAL PRIMARY KEY,
            recipient_email VARCHAR NOT NULL,
            recipient_name VARCHAR,
            subject VARCHAR NOT NULL,
            template_type VARCHAR,
            status VARCHAR NOT NULL,
            error_message TEXT,
            sent_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
        """
    ))
    await conn.execute(text(
        """
        CREATE INDEX IF NOT EXISTS idx_email_log_recipient ON email_logs (recipient_email)
        """
    ))
    await conn.execute(text(
        """
        CREATE INDEX IF NOT EXISTS idx_email_log_status ON email_logs (status)
        """
    ))
    await conn.execute(text(
        """
        CREATE INDEX IF NOT EXISTS idx_email_log_template ON email_logs (template_type)
        """
    ))
    await conn.execute(text(
        """
        CREATE INDEX IF NOT EXISTS idx_email_log_created ON email_logs (created_at)
        """
    ))
    print("✅ Email logs table created")


async def create_employee_details_table(conn):
    print("📝 Creating employee_details table...")
    await conn.execute(text(
        """
        CREATE TABLE IF NOT EXISTS employee_details (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
            employee_id VARCHAR UNIQUE,
            date_of_birth DATE,
            gender VARCHAR,
            marital_status VARCHAR,
            nationality VARCHAR,
            personal_email VARCHAR,
            emergency_contact_name VARCHAR,
            emergency_contact_phone VARCHAR,
            emergency_contact_relation VARCHAR,
            current_address TEXT,
            permanent_address TEXT,
            city VARCHAR,
            state VARCHAR,
            postal_code VARCHAR,
            country VARCHAR,
            department VARCHAR,
            manager_id INTEGER REFERENCES users(id),
            employment_type VARCHAR,
            work_location VARCHAR,
            work_schedule VARCHAR,
            basic_salary VARCHAR,
            currency VARCHAR DEFAULT 'INR',
            bank_name VARCHAR,
            bank_account_number VARCHAR,
            ifsc_code VARCHAR,
            skills TEXT,
            certifications TEXT,
            education_qualification VARCHAR,
            previous_experience_years INTEGER,
            probation_period_months INTEGER DEFAULT 6,
            probation_start_date DATE,
            probation_end_date DATE,
            probation_status VARCHAR DEFAULT 'pending',
            probation_review_date DATE,
            probation_review_notes TEXT,
            probation_reviewer_id INTEGER REFERENCES users(id),
            termination_date DATE,
            termination_reason VARCHAR,
            termination_type VARCHAR,
            termination_notice_period_days INTEGER,
            last_working_date DATE,
            termination_notes TEXT,
            termination_initiated_by INTEGER REFERENCES users(id),
            exit_interview_date DATE,
            exit_interview_notes TEXT,
            clearance_status VARCHAR DEFAULT 'pending',
            final_settlement_amount VARCHAR,
            final_settlement_date DATE,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE
        )
        """
    ))
    # Create indexes for employee_details
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_employee_user_id ON employee_details (user_id)",
        "CREATE INDEX IF NOT EXISTS idx_employee_employee_id ON employee_details (employee_id)",
        "CREATE INDEX IF NOT EXISTS idx_employee_department ON employee_details (department)",
        "CREATE INDEX IF NOT EXISTS idx_employee_manager ON employee_details (manager_id)",
        "CREATE INDEX IF NOT EXISTS idx_employee_active ON employee_details (is_active)",
        "CREATE INDEX IF NOT EXISTS idx_employee_created_at ON employee_details (created_at)",
        "CREATE INDEX IF NOT EXISTS idx_employee_probation_status ON employee_details (probation_status)",
        "CREATE INDEX IF NOT EXISTS idx_employee_probation_end_date ON employee_details (probation_end_date)",
        "CREATE INDEX IF NOT EXISTS idx_employee_termination_date ON employee_details (termination_date)",
        "CREATE INDEX IF NOT EXISTS idx_employee_clearance_status ON employee_details (clearance_status)"
    ]
    for index_sql in indexes:
        await conn.execute(text(index_sql))
    print("✅ Employee details table created")


async def create_employment_history_table(conn):
    print("📝 Creating employment_history table...")
    await conn.execute(text(
        """
        CREATE TABLE IF NOT EXISTS employment_history (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            position_title VARCHAR NOT NULL,
            department VARCHAR,
            employment_type VARCHAR,
            work_location VARCHAR,
            start_date DATE NOT NULL,
            end_date DATE,
            salary VARCHAR,
            currency VARCHAR DEFAULT 'INR',
            manager_id INTEGER REFERENCES users(id),
            reporting_manager_name VARCHAR,
            status VARCHAR,
            reason_for_change TEXT,
            notes TEXT,
            is_current BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE
        )
        """
    ))
    # Create indexes for employment_history
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_employment_user_id ON employment_history (user_id)",
        "CREATE INDEX IF NOT EXISTS idx_employment_position ON employment_history (position_title)",
        "CREATE INDEX IF NOT EXISTS idx_employment_department ON employment_history (department)",
        "CREATE INDEX IF NOT EXISTS idx_employment_dates ON employment_history (start_date, end_date)",
        "CREATE INDEX IF NOT EXISTS idx_employment_current ON employment_history (is_current)",
        "CREATE INDEX IF NOT EXISTS idx_employment_manager ON employment_history (manager_id)",
        "CREATE INDEX IF NOT EXISTS idx_employment_created_at ON employment_history (created_at)"
    ]
    for index_sql in indexes:
        await conn.execute(text(index_sql))
    print("✅ Employment history table created")


async def create_tasks_table(conn):
    print("📝 Creating tasks table...")
    await conn.execute(text(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            name VARCHAR NOT NULL,
            description TEXT,
            status VARCHAR DEFAULT 'pending' NOT NULL,
            due_date TIMESTAMP WITH TIME ZONE,
            completed_at TIMESTAMP WITH TIME ZONE,
            priority VARCHAR DEFAULT 'medium',
            category VARCHAR,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE
        )
        """
    ))
    # Create indexes for tasks
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_task_user_id ON tasks (user_id)",
        "CREATE INDEX IF NOT EXISTS idx_task_status ON tasks (status)",
        "CREATE INDEX IF NOT EXISTS idx_task_priority ON tasks (priority)",
        "CREATE INDEX IF NOT EXISTS idx_task_category ON tasks (category)",
        "CREATE INDEX IF NOT EXISTS idx_task_due_date ON tasks (due_date)",
        "CREATE INDEX IF NOT EXISTS idx_task_active ON tasks (is_active)",
        "CREATE INDEX IF NOT EXISTS idx_task_created_at ON tasks (created_at)",
        "CREATE INDEX IF NOT EXISTS idx_task_user_status ON tasks (user_id, status)",
        "CREATE INDEX IF NOT EXISTS idx_task_user_created ON tasks (user_id, created_at)"
    ]
    for index_sql in indexes:
        await conn.execute(text(index_sql))
    print("✅ Tasks table created")


async def create_missing_tables(engine):
    print("🛠️ Creating base tables from models...")
    try:
        from app.models import Base  # import here to avoid hard dependency if not needed
        print("📦 Successfully imported models")
    except Exception as e:
        print(f"⚠️ Could not import app.models.Base: {e}")
        print("🔄 Creating base tables manually...")
        await create_base_tables_manually(engine)
        return
    
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Base tables created from SQLAlchemy metadata")
    except Exception as e:
        print(f"⚠️ SQLAlchemy metadata creation failed: {e}")
        print("🔄 Falling back to manual table creation...")
        await create_base_tables_manually(engine)


async def create_base_tables_manually(engine):
    """Create base tables manually if SQLAlchemy metadata fails"""
    async with engine.begin() as conn:
        # Create users table
        await conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR UNIQUE NOT NULL,
                hashed_password VARCHAR NOT NULL,
                name VARCHAR NOT NULL,
                phone VARCHAR,
                role VARCHAR DEFAULT 'user' NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE
            )
            """
        ))
        
        # Create leaves table
        await conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS leaves (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                start_date TIMESTAMP WITH TIME ZONE NOT NULL,
                end_date TIMESTAMP WITH TIME ZONE NOT NULL,
                total_days NUMERIC(4,1) NOT NULL,
                reason TEXT NOT NULL,
                status VARCHAR DEFAULT 'pending' NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE
            )
            """
        ))
        
        # Create holidays table
        await conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS holidays (
                id SERIAL PRIMARY KEY,
                date TIMESTAMP WITH TIME ZONE NOT NULL,
                title VARCHAR NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE
            )
            """
        ))
        
        # Create tasks table
        await conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                name VARCHAR NOT NULL,
                description TEXT,
                status VARCHAR DEFAULT 'pending' NOT NULL,
                due_date TIMESTAMP WITH TIME ZONE,
                completed_at TIMESTAMP WITH TIME ZONE,
                priority VARCHAR DEFAULT 'medium',
                category VARCHAR,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE
            )
            """
        ))
        
        print("✅ Base tables created manually")


async def verify(conn):
    print("🔍 Verifying all tables and key columns...")
    
    # Check if all tables exist
    tables_query = text(
        """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN ('users', 'leaves', 'holidays', 'email_settings', 'email_templates', 'email_logs', 'employee_details', 'employment_history', 'tasks')
        ORDER BY table_name
        """
    )
    tables = (await conn.execute(tables_query)).fetchall()
    print("📋 Existing tables:")
    for table in tables:
        print(f"   ✅ {table[0]}")
    
    # Check key columns
    verify_query = text(
        """
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE (table_name = 'users' AND column_name IN (
                 'designation','joining_date','wifi_user_id','profile_image','aadhaar_front','aadhaar_back','pan_image',
                 'profile_image_status','aadhaar_front_status','aadhaar_back_status','pan_image_status'
             ))
           OR (table_name = 'holidays' AND column_name = 'is_active')
           OR (table_name = 'leaves' AND column_name = 'total_days')
           OR (table_name = 'email_settings' AND column_name = 'smtp_server')
           OR (table_name = 'email_templates' AND column_name = 'name')
           OR (table_name = 'email_logs' AND column_name = 'recipient_email')
           OR (table_name = 'employee_details' AND column_name = 'user_id')
           OR (table_name = 'employment_history' AND column_name = 'user_id')
           OR (table_name = 'tasks' AND column_name = 'user_id')
        ORDER BY table_name, column_name
        """
    )
    rows = (await conn.execute(verify_query)).fetchall()
    print("🔍 Key columns verified:")
    for tbl, col, dtype in rows:
        print(f"   - {tbl}.{col}: {dtype}")


async def run_migration():
    database_url = get_database_url()
    engine = create_async_engine(database_url, echo=False)
    print("Connecting to database...")
    
    # First, create all base tables from SQLAlchemy metadata
    print("Creating base tables from models...")
    await create_missing_tables(engine)
    
    # Then modify existing tables and add new ones
    async with engine.begin() as conn:
        print("Connected successfully!")
        
        # Core table modifications
        await ensure_user_columns(conn)
        await ensure_holiday_is_active(conn)
        await ensure_identity_document_columns(conn)
        await ensure_leaves_total_days_numeric(conn)
        
        # Email management tables
        await create_email_settings_table(conn)
        await create_email_template_table(conn)
        await create_email_log_table(conn)
        
        # Employee management tables
        await create_employee_details_table(conn)
        await create_employment_history_table(conn)
        
        # Task management table
        await create_tasks_table(conn)
        
        # Verification
        await verify(conn)
    
    await engine.dispose()
    print("\n🎉 Migration completed successfully!")
    print("📋 All tables created/updated:")
    print("   ✅ users (with identity documents)")
    print("   ✅ leaves (with half-day support)")
    print("   ✅ holidays (with active status)")
    print("   ✅ email_settings")
    print("   ✅ email_templates")
    print("   ✅ email_logs")
    print("   ✅ employee_details")
    print("   ✅ employment_history")
    print("   ✅ tasks (task management)")
    print("\n🚀 You can now restart your backend server.")


if __name__ == "__main__":
    asyncio.run(run_migration())
