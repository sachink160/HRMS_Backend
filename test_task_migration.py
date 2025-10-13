#!/usr/bin/env python3
"""
Test script to verify the Task migration works correctly
"""

import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

load_dotenv()

def get_database_url() -> str:
    """Get database URL from environment or use default"""
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url
    return "postgresql+asyncpg://postgres:dwij9143@localhost:5432/hrms_db"

async def test_task_table():
    """Test if the tasks table was created correctly"""
    database_url = get_database_url()
    engine = create_async_engine(database_url, echo=False)
    
    try:
        async with engine.begin() as conn:
            print("🔍 Testing Task table creation...")
            
            # Check if tasks table exists
            result = await conn.execute(text(
                """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'tasks'
                """
            ))
            table_exists = result.fetchone() is not None
            
            if table_exists:
                print("✅ Tasks table exists")
                
                # Check table structure
                result = await conn.execute(text(
                    """
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = 'tasks'
                    ORDER BY ordinal_position
                    """
                ))
                columns = result.fetchall()
                
                print("📋 Tasks table structure:")
                for col_name, data_type, nullable, default in columns:
                    print(f"   - {col_name}: {data_type} {'NULL' if nullable == 'YES' else 'NOT NULL'} {f'DEFAULT {default}' if default else ''}")
                
                # Check indexes
                result = await conn.execute(text(
                    """
                    SELECT indexname, indexdef
                    FROM pg_indexes
                    WHERE tablename = 'tasks'
                    ORDER BY indexname
                    """
                ))
                indexes = result.fetchall()
                
                print("🔍 Tasks table indexes:")
                for idx_name, idx_def in indexes:
                    print(f"   - {idx_name}")
                
                # Test inserting a sample task (if users table has data)
                user_result = await conn.execute(text("SELECT id FROM users LIMIT 1"))
                user_row = user_result.fetchone()
                
                if user_row:
                    user_id = user_row[0]
                    print(f"🧪 Testing task insertion with user_id: {user_id}")
                    
                    await conn.execute(text(
                        """
                        INSERT INTO tasks (user_id, name, description, status, priority, category)
                        VALUES (:user_id, :name, :description, :status, :priority, :category)
                        """,
                        {
                            "user_id": user_id,
                            "name": "Test Task",
                            "description": "This is a test task created during migration verification",
                            "status": "pending",
                            "priority": "medium",
                            "category": "test"
                        }
                    )
                    
                    # Verify the insertion
                    result = await conn.execute(text(
                        "SELECT id, name, status, priority FROM tasks WHERE name = 'Test Task'"
                    ))
                    task_row = result.fetchone()
                    
                    if task_row:
                        print(f"✅ Test task created successfully: ID={task_row[0]}, Name={task_row[1]}, Status={task_row[2]}, Priority={task_row[3]}")
                        
                        # Clean up test task
                        await conn.execute(text("DELETE FROM tasks WHERE name = 'Test Task'"))
                        print("🧹 Test task cleaned up")
                    else:
                        print("❌ Failed to verify task insertion")
                else:
                    print("⚠️ No users found in database - skipping task insertion test")
                
            else:
                print("❌ Tasks table does not exist")
                return False
                
    except Exception as e:
        print(f"❌ Error testing tasks table: {str(e)}")
        return False
    finally:
        await engine.dispose()
    
    return True

async def main():
    """Main test function"""
    print("🚀 Testing Task Migration")
    print("=" * 40)
    
    success = await test_task_table()
    
    if success:
        print("\n🎉 Task migration test completed successfully!")
        print("✅ Tasks table is properly created and functional")
    else:
        print("\n❌ Task migration test failed!")
        print("Please check the migration script and database connection")

if __name__ == "__main__":
    asyncio.run(main())
