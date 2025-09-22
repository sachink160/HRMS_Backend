"""
Simple script to add the missing columns to the database
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def run_migration():
    # Get database URL
    database_url = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://postgres:dwij9143@localhost:5432/hrms_db"
    )
    
    # Convert to sync format
    sync_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    
    try:
        print("🔗 Connecting to database...")
        conn = await asyncpg.connect(sync_url)
        print("✅ Connected successfully!")
        
        # Add designation column
        print("📝 Adding designation column...")
        await conn.execute("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS designation VARCHAR(255) NULL
        """)
        print("✅ designation column added!")
        
        # Add joining_date column
        print("📝 Adding joining_date column...")
        await conn.execute("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS joining_date DATE NULL
        """)
        print("✅ joining_date column added!")
        
        # Add is_active to holidays
        print("📝 Adding is_active column to holidays...")
        await conn.execute("""
            ALTER TABLE holidays
            ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE
        """)
        # Ensure existing NULLs are set to TRUE
        await conn.execute("""
            UPDATE holidays SET is_active = TRUE WHERE is_active IS NULL
        """)
        print("✅ is_active column added/updated on holidays!")
        
        # Add wifi_user_id column to users
        print("📝 Adding wifi_user_id column to users...")
        await conn.execute("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS wifi_user_id VARCHAR(255) NULL
        """)
        # Add index for wifi_user_id
        await conn.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_indexes WHERE tablename = 'users' AND indexname = 'ix_users_wifi_user_id'
                ) THEN
                    CREATE INDEX ix_users_wifi_user_id ON users (wifi_user_id);
                END IF;
            END$$;
        """)
        print("✅ wifi_user_id column (and index) added!")

        # Verify columns exist
        print("🔍 Verifying columns...")
        columns = await conn.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name IN ('designation', 'joining_date', 'wifi_user_id')
            ORDER BY column_name
        """)
        
        if columns:
            print("✅ New columns verified:")
            for col in columns:
                print(f"   - {col['column_name']}: {col['data_type']}")
        else:
            print("❌ Columns not found!")
        
        await conn.close()
        print("\n🎉 Migration completed successfully!")
        print("You can now restart your backend server.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure PostgreSQL is running")
        print("2. Check if database 'hrms_db' exists")
        print("3. Verify connection credentials")

if __name__ == "__main__":
    asyncio.run(run_migration())
