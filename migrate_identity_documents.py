#!/usr/bin/env python3
"""
Migration script to add identity document fields to the users table.
Run this script after updating the models to add the new columns.
"""

import asyncio
import sys
from sqlalchemy import text
from app.database import engine
from app.logger import log_info, log_error

async def migrate_identity_documents():
    """Add identity document fields to users table."""
    try:
        log_info("Starting identity documents migration...")
        
        async with engine.begin() as conn:
            # Add the new columns to the users table
            await conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS profile_image VARCHAR,
                ADD COLUMN IF NOT EXISTS aadhaar_front VARCHAR,
                ADD COLUMN IF NOT EXISTS aadhaar_back VARCHAR,
                ADD COLUMN IF NOT EXISTS pan_image VARCHAR,
                ADD COLUMN IF NOT EXISTS profile_image_status VARCHAR,
                ADD COLUMN IF NOT EXISTS aadhaar_front_status VARCHAR,
                ADD COLUMN IF NOT EXISTS aadhaar_back_status VARCHAR,
                ADD COLUMN IF NOT EXISTS pan_image_status VARCHAR
            """))
            
            log_info("Identity document fields added successfully!")
            
    except Exception as e:
        log_error(f"Migration failed: {str(e)}")
        raise

async def rollback_identity_documents():
    """Remove identity document fields from users table."""
    try:
        log_info("Rolling back identity documents migration...")
        
        async with engine.begin() as conn:
            # Remove the columns from the users table
            await conn.execute(text("""
                ALTER TABLE users 
                DROP COLUMN IF EXISTS profile_image,
                DROP COLUMN IF EXISTS aadhaar_front,
                DROP COLUMN IF EXISTS aadhaar_back,
                DROP COLUMN IF EXISTS pan_image,
                DROP COLUMN IF EXISTS profile_image_status,
                DROP COLUMN IF EXISTS aadhaar_front_status,
                DROP COLUMN IF EXISTS aadhaar_back_status,
                DROP COLUMN IF EXISTS pan_image_status
            """))
            
            log_info("Identity document fields removed successfully!")
            
    except Exception as e:
        log_error(f"Rollback failed: {str(e)}")
        raise

async def main():
    """Main migration function."""
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        await rollback_identity_documents()
    else:
        await migrate_identity_documents()

if __name__ == "__main__":
    asyncio.run(main())
