#!/usr/bin/env python3
"""
Script to fix invalid email addresses in the HRMS database
This script finds and updates users with invalid email addresses to valid ones.
"""

import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

try:
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


async def find_invalid_emails(conn):
    """Find users with invalid email addresses."""
    print("🔍 Searching for users with invalid email addresses...")
    
    # Common invalid patterns
    invalid_patterns = [
        "%@%.local",
        "%@localhost",
        "%@%.invalid",
        "%@%.test",
        "%@%.example"
    ]
    
    invalid_users = []
    for pattern in invalid_patterns:
        result = await conn.execute(text(
            f"SELECT id, email, name FROM users WHERE email LIKE '{pattern}'"
        ))
        users = result.fetchall()
        invalid_users.extend(users)
    
    # Also check for emails without @ symbol
    result = await conn.execute(text(
        "SELECT id, email, name FROM users WHERE email NOT LIKE '%@%'"
    ))
    users = result.fetchall()
    invalid_users.extend(users)
    
    return invalid_users


async def fix_invalid_emails(conn, invalid_users):
    """Fix invalid email addresses."""
    if not invalid_users:
        print("✅ No invalid email addresses found!")
        return
    
    print(f"❌ Found {len(invalid_users)} users with invalid email addresses:")
    for user_id, email, name in invalid_users:
        print(f"   - ID: {user_id}, Email: {email}, Name: {name}")
    
    print("\n🔧 Fixing invalid email addresses...")
    
    for user_id, old_email, name in invalid_users:
        # Generate a valid email based on the user's name or ID
        if "@" in old_email:
            # Extract the part before @ and use a valid domain
            username = old_email.split("@")[0]
            new_email = f"{username}@hrms.com"
        else:
            # Use user ID or name to create a valid email
            username = name.lower().replace(" ", ".") if name else f"user{user_id}"
            new_email = f"{username}@hrms.com"
        
        # Ensure uniqueness
        counter = 1
        original_new_email = new_email
        while True:
            result = await conn.execute(text(
                "SELECT COUNT(*) FROM users WHERE email = :email"
            ), {"email": new_email})
            count = result.scalar()
            if count == 0:
                break
            new_email = f"{original_new_email.split('@')[0]}{counter}@hrms.com"
            counter += 1
        
        # Update the email
        await conn.execute(text(
            "UPDATE users SET email = :new_email WHERE id = :user_id"
        ), {"new_email": new_email, "user_id": user_id})
        
        print(f"   ✅ Updated user {user_id}: {old_email} → {new_email}")


async def main():
    """Main function to fix invalid emails."""
    database_url = get_database_url()
    engine = create_async_engine(database_url, echo=False)
    
    print("🔗 Connecting to database...")
    async with engine.begin() as conn:
        print("✅ Connected successfully!")
        
        # Find invalid emails
        invalid_users = await find_invalid_emails(conn)
        
        # Fix invalid emails
        await fix_invalid_emails(conn, invalid_users)
        
        print("\n🎉 Email validation fix completed!")
        print("All users now have valid email addresses.")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
