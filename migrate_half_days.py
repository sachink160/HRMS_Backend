#!/usr/bin/env python3
"""
Migration script to change total_days field from INTEGER to DECIMAL for half-day support
Run this script from the Backend directory: python migrate_half_days.py
"""

import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL from environment or default
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://postgres:dwij9143@localhost:5432/hrms_db"
)

async def migrate_half_days():
    """Change total_days column from INTEGER to DECIMAL for half-day support"""
    
    # Create database engine
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        try:
            print("Starting migration: Converting total_days to support half-days...")
            
            # Check if column exists and its current type
            check_column_query = text("""
                SELECT column_name, data_type, numeric_precision, numeric_scale
                FROM information_schema.columns 
                WHERE table_name = 'leaves' 
                AND column_name = 'total_days'
            """)
            
            result = await conn.execute(check_column_query)
            column_info = result.fetchone()
            
            if not column_info:
                print("Column 'total_days' does not exist in leaves table. Please run the initial migration first.")
                return
            
            current_type = column_info[1]
            print(f"Current total_days column type: {current_type}")
            
            if current_type == 'numeric':
                print("Column 'total_days' is already DECIMAL type. No migration needed.")
                return
            
            # Convert INTEGER to DECIMAL(4,1) to support half-days
            alter_column_query = text("""
                ALTER TABLE leaves 
                ALTER COLUMN total_days TYPE NUMERIC(4,1)
            """)
            
            await conn.execute(alter_column_query)
            print("✓ Converted total_days column to DECIMAL(4,1) for half-day support")
            
            # Update any existing integer values to decimal format
            update_existing_query = text("""
                UPDATE leaves 
                SET total_days = total_days::NUMERIC(4,1)
                WHERE total_days IS NOT NULL
            """)
            
            result = await conn.execute(update_existing_query)
            print(f"✓ Updated {result.rowcount} existing leave records to decimal format")
            
            print("Migration completed successfully!")
            print("Now you can use half-day values like 1.5, 2.5, 4.5, etc.")
            
        except Exception as e:
            print(f"Migration failed: {str(e)}")
            raise
        finally:
            await conn.commit()

async def rollback_half_days():
    """Rollback: Convert total_days back to INTEGER (loses half-day data)"""
    
    # Create database engine
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        try:
            print("Starting rollback: Converting total_days back to INTEGER...")
            print("WARNING: This will round half-day values to whole numbers!")
            
            # Check if column exists and its current type
            check_column_query = text("""
                SELECT column_name, data_type
                FROM information_schema.columns 
                WHERE table_name = 'leaves' 
                AND column_name = 'total_days'
            """)
            
            result = await conn.execute(check_column_query)
            column_info = result.fetchone()
            
            if not column_info:
                print("Column 'total_days' does not exist in leaves table.")
                return
            
            current_type = column_info[1]
            print(f"Current total_days column type: {current_type}")
            
            if current_type == 'integer':
                print("Column 'total_days' is already INTEGER type. No rollback needed.")
                return
            
            # Round any half-day values to whole numbers first
            round_values_query = text("""
                UPDATE leaves 
                SET total_days = ROUND(total_days)
                WHERE total_days % 1 != 0
            """)
            
            result = await conn.execute(round_values_query)
            print(f"✓ Rounded {result.rowcount} half-day values to whole numbers")
            
            # Convert DECIMAL back to INTEGER
            alter_column_query = text("""
                ALTER TABLE leaves 
                ALTER COLUMN total_days TYPE INTEGER
            """)
            
            await conn.execute(alter_column_query)
            print("✓ Converted total_days column back to INTEGER")
            
            print("Rollback completed successfully!")
            print("Half-day support has been removed.")
            
        except Exception as e:
            print(f"Rollback failed: {str(e)}")
            raise
        finally:
            await conn.commit()

async def main():
    """Main migration function"""
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        await rollback_half_days()
    else:
        await migrate_half_days()

if __name__ == "__main__":
    asyncio.run(main())
