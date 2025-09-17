#!/usr/bin/env python3
"""
Database optimization script for HRMS.
This script applies database indexes and optimizations.
"""

import asyncio
import sys
from sqlalchemy import text
from app.database import engine
from app.logger import log_info, log_error

async def create_indexes():
    """Create database indexes for performance optimization."""
    
    indexes = [
        # User table indexes
        "CREATE INDEX IF NOT EXISTS idx_user_role ON users(role);",
        "CREATE INDEX IF NOT EXISTS idx_user_active ON users(is_active);",
        "CREATE INDEX IF NOT EXISTS idx_user_created_at ON users(created_at);",
        "CREATE INDEX IF NOT EXISTS idx_user_role_active ON users(role, is_active);",
        
        # Leave table indexes
        "CREATE INDEX IF NOT EXISTS idx_leave_user_id ON leaves(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_leave_status ON leaves(status);",
        "CREATE INDEX IF NOT EXISTS idx_leave_dates ON leaves(start_date, end_date);",
        "CREATE INDEX IF NOT EXISTS idx_leave_user_status ON leaves(user_id, status);",
        "CREATE INDEX IF NOT EXISTS idx_leave_created_at ON leaves(created_at);",
        "CREATE INDEX IF NOT EXISTS idx_leave_user_created ON leaves(user_id, created_at);",
        
        # Holiday table indexes
        "CREATE INDEX IF NOT EXISTS idx_holiday_date ON holidays(date);",
        "CREATE INDEX IF NOT EXISTS idx_holiday_active ON holidays(is_active);",
        "CREATE INDEX IF NOT EXISTS idx_holiday_date_active ON holidays(date, is_active);",
        
        # UserTracker table indexes
        "CREATE INDEX IF NOT EXISTS idx_tracker_user_id ON user_trackers(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_tracker_date ON user_trackers(date);",
        "CREATE INDEX IF NOT EXISTS idx_tracker_user_date ON user_trackers(user_id, date);",
        "CREATE INDEX IF NOT EXISTS idx_tracker_check_in ON user_trackers(check_in);",
        "CREATE INDEX IF NOT EXISTS idx_tracker_user_checkin ON user_trackers(user_id, check_in);",
    ]
    
    try:
        async with engine.begin() as conn:
            log_info("Starting database optimization...")
            
            for i, index_sql in enumerate(indexes, 1):
                try:
                    await conn.execute(text(index_sql))
                    log_info(f"Created index {i}/{len(indexes)}")
                except Exception as e:
                    log_error(f"Failed to create index {i}: {str(e)}")
                    # Continue with other indexes even if one fails
                    continue
            
            # Update table statistics for better query planning
            await conn.execute(text("ANALYZE users;"))
            await conn.execute(text("ANALYZE leaves;"))
            await conn.execute(text("ANALYZE holidays;"))
            await conn.execute(text("ANALYZE user_trackers;"))
            
            log_info("Database optimization completed successfully!")
            
    except Exception as e:
        log_error(f"Database optimization failed: {str(e)}")
        raise

async def check_indexes():
    """Check if indexes were created successfully."""
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("""
                SELECT schemaname, tablename, indexname, indexdef 
                FROM pg_indexes 
                WHERE schemaname = 'public' 
                AND indexname LIKE 'idx_%'
                ORDER BY tablename, indexname;
            """))
            
            indexes = result.fetchall()
            log_info(f"Found {len(indexes)} optimization indexes:")
            
            for index in indexes:
                log_info(f"  - {index.indexname} on {index.tablename}")
                
    except Exception as e:
        log_error(f"Failed to check indexes: {str(e)}")

async def main():
    """Main function."""
    try:
        log_info("HRMS Database Optimization Script")
        log_info("=" * 50)
        
        # Create indexes
        await create_indexes()
        
        # Check indexes
        await check_indexes()
        
        log_info("Optimization completed successfully!")
        
    except Exception as e:
        log_error(f"Optimization failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
