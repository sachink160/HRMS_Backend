#!/usr/bin/env python3
"""
Migration script to add Employee Details and Employment History tables to HRMS database.
This script creates the new tables for comprehensive employee tracking.
"""

import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.database import DATABASE_URL
from app.models import Base, EmployeeDetails, EmploymentHistory
from app.logger import log_info, log_error

async def create_employee_tables():
    """Create employee details and employment history tables."""
    try:
        # Create async engine
        engine = create_async_engine(DATABASE_URL, echo=True)
        
        log_info("Starting employee tables migration...")
        
        async with engine.begin() as conn:
            # Create the new tables
            await conn.run_sync(Base.metadata.create_all)
            log_info("Employee tables created successfully")
            
            # Verify tables were created
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('employee_details', 'employment_history')
                ORDER BY table_name;
            """))
            
            tables = result.fetchall()
            log_info(f"Created tables: {[table[0] for table in tables]}")
            
            # Check indexes
            index_result = await conn.execute(text("""
                SELECT indexname, tablename 
                FROM pg_indexes 
                WHERE tablename IN ('employee_details', 'employment_history')
                ORDER BY tablename, indexname;
            """))
            
            indexes = index_result.fetchall()
            log_info(f"Created indexes: {[(idx[0], idx[1]) for idx in indexes]}")
        
        await engine.dispose()
        log_info("Employee tables migration completed successfully")
        
    except Exception as e:
        log_error(f"Migration failed: {str(e)}")
        raise

async def verify_migration():
    """Verify that the migration was successful."""
    try:
        engine = create_async_engine(DATABASE_URL, echo=False)
        
        async with engine.begin() as conn:
            # Check if tables exist and have correct structure
            tables_to_check = ['employee_details', 'employment_history']
            
            for table_name in tables_to_check:
                # Check table exists
                result = await conn.execute(text(f"""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = '{table_name}';
                """))
                
                if result.scalar() == 0:
                    raise Exception(f"Table {table_name} was not created")
                
                # Check columns
                columns_result = await conn.execute(text(f"""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = '{table_name}'
                    ORDER BY ordinal_position;
                """))
                
                columns = columns_result.fetchall()
                log_info(f"Table {table_name} columns: {[(col[0], col[1], col[2]) for col in columns]}")
            
            log_info("Migration verification completed successfully")
        
        await engine.dispose()
        
    except Exception as e:
        log_error(f"Migration verification failed: {str(e)}")
        raise

async def main():
    """Main migration function."""
    try:
        log_info("Starting HRMS Employee Tables Migration")
        
        # Create tables
        await create_employee_tables()
        
        # Verify migration
        await verify_migration()
        
        log_info("Migration completed successfully!")
        print("✅ Employee tables migration completed successfully!")
        print("📊 Created tables:")
        print("   - employee_details (comprehensive employee information)")
        print("   - employment_history (job changes and promotions)")
        print("🔗 New API endpoints available:")
        print("   - /employees/details - Employee details management")
        print("   - /employees/history - Employment history management")
        print("   - /employees/summary - Employee summary with tracking")
        print("   - /trackers/employee-summary - Enhanced tracking with employee data")
        
    except Exception as e:
        log_error(f"Migration failed: {str(e)}")
        print(f"❌ Migration failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
