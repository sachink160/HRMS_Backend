#!/usr/bin/env python3
"""
Migration script to add probation and termination management fields to EmployeeDetails table.
Run this script to update the database schema.
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))

from sqlalchemy import text
from app.database import get_async_engine
from app.logger import log_info, log_error

async def migrate_probation_termination():
    """Add probation and termination fields to employee_details table."""
    engine = get_async_engine()
    
    try:
        async with engine.begin() as conn:
            # Add probation management fields
            log_info("Adding probation management fields...")
            
            probation_fields = [
                "probation_period_months INTEGER DEFAULT 6",
                "probation_start_date DATE",
                "probation_end_date DATE", 
                "probation_status VARCHAR(20) DEFAULT 'pending'",
                "probation_review_date DATE",
                "probation_review_notes TEXT",
                "probation_reviewer_id INTEGER REFERENCES users(id)"
            ]
            
            for field in probation_fields:
                try:
                    await conn.execute(text(f"ALTER TABLE employee_details ADD COLUMN {field}"))
                    log_info(f"Added field: {field}")
                except Exception as e:
                    if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                        log_info(f"Field already exists: {field}")
                    else:
                        log_error(f"Error adding field {field}: {e}")
            
            # Add termination management fields
            log_info("Adding termination management fields...")
            
            termination_fields = [
                "termination_date DATE",
                "termination_reason VARCHAR(100)",
                "termination_type VARCHAR(20)",
                "termination_notice_period_days INTEGER",
                "last_working_date DATE",
                "termination_notes TEXT",
                "termination_initiated_by INTEGER REFERENCES users(id)",
                "exit_interview_date DATE",
                "exit_interview_notes TEXT",
                "clearance_status VARCHAR(20) DEFAULT 'pending'",
                "final_settlement_amount VARCHAR(50)",
                "final_settlement_date DATE"
            ]
            
            for field in termination_fields:
                try:
                    await conn.execute(text(f"ALTER TABLE employee_details ADD COLUMN {field}"))
                    log_info(f"Added field: {field}")
                except Exception as e:
                    if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                        log_info(f"Field already exists: {field}")
                    else:
                        log_error(f"Error adding field {field}: {e}")
            
            # Add indexes for performance
            log_info("Adding indexes...")
            
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_employee_probation_status ON employee_details(probation_status)",
                "CREATE INDEX IF NOT EXISTS idx_employee_probation_end_date ON employee_details(probation_end_date)",
                "CREATE INDEX IF NOT EXISTS idx_employee_termination_date ON employee_details(termination_date)",
                "CREATE INDEX IF NOT EXISTS idx_employee_clearance_status ON employee_details(clearance_status)"
            ]
            
            for index in indexes:
                try:
                    await conn.execute(text(index))
                    log_info(f"Added index: {index}")
                except Exception as e:
                    log_error(f"Error adding index: {e}")
            
            log_info("Migration completed successfully!")
            
    except Exception as e:
        log_error(f"Migration failed: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    print("Starting probation and termination migration...")
    asyncio.run(migrate_probation_termination())
    print("Migration completed!")
