#!/usr/bin/env python3
"""
Migration script to add total_days field to leaves table
"""

import asyncio
import sys
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import DATABASE_URL

async def migrate_total_days():
    """Add total_days column to leaves table"""
    
    # Create database engine
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        try:
            print("Starting migration: Adding total_days field to leaves table...")
            
            # Check if column already exists
            check_column_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'leaves' 
                AND column_name = 'total_days'
            """)
            
            result = await conn.execute(check_column_query)
            column_exists = result.fetchone() is not None
            
            if column_exists:
                print("Column 'total_days' already exists in leaves table. Skipping migration.")
                return
            
            # Add total_days column
            add_column_query = text("""
                ALTER TABLE leaves 
                ADD COLUMN total_days INTEGER NOT NULL DEFAULT 1
            """)
            
            await conn.execute(add_column_query)
            print("✓ Added total_days column to leaves table")
            
            # Update existing records with calculated days
            update_existing_query = text("""
                UPDATE leaves 
                SET total_days = EXTRACT(DAY FROM (end_date - start_date)) + 1
                WHERE total_days = 1
            """)
            
            result = await conn.execute(update_existing_query)
            print(f"✓ Updated {result.rowcount} existing leave records with calculated days")
            
            # Remove default value constraint
            remove_default_query = text("""
                ALTER TABLE leaves 
                ALTER COLUMN total_days DROP DEFAULT
            """)
            
            await conn.execute(remove_default_query)
            print("✓ Removed default value constraint from total_days column")
            
            print("Migration completed successfully!")
            
        except Exception as e:
            print(f"Migration failed: {str(e)}")
            raise
        finally:
            await conn.commit()

async def rollback_total_days():
    """Rollback: Remove total_days column from leaves table"""
    
    # Create database engine
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        try:
            print("Starting rollback: Removing total_days field from leaves table...")
            
            # Check if column exists
            check_column_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'leaves' 
                AND column_name = 'total_days'
            """)
            
            result = await conn.execute(check_column_query)
            column_exists = result.fetchone() is not None
            
            if not column_exists:
                print("Column 'total_days' does not exist in leaves table. Nothing to rollback.")
                return
            
            # Remove total_days column
            remove_column_query = text("""
                ALTER TABLE leaves 
                DROP COLUMN total_days
            """)
            
            await conn.execute(remove_column_query)
            print("✓ Removed total_days column from leaves table")
            
            print("Rollback completed successfully!")
            
        except Exception as e:
            print(f"Rollback failed: {str(e)}")
            raise
        finally:
            await conn.commit()

async def main():
    """Main migration function"""
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        await rollback_total_days()
    else:
        await migrate_total_days()

if __name__ == "__main__":
    asyncio.run(main())
