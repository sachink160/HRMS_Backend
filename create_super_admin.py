#!/usr/bin/env python3
"""
Script to create a super admin user in the HRMS database
This script can be run independently to add a super admin user.
"""

import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models import User, UserRole
from app.auth import get_password_hash
from app.database import DATABASE_URL

load_dotenv()

async def create_super_admin():
    """Create super admin user in the database."""
    print("Starting super admin creation process...")
    print(f"Database URL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'Local database'}")
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    # Create async session factory
    AsyncSessionLocal = sessionmaker(
        engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    try:
        # Test database connection
        async with engine.begin() as conn:
            await conn.execute(select(1))
        print("Database connection successful")
        
        async with AsyncSessionLocal() as session:
            # Resolve credentials from env with sensible defaults
            admin_email = os.getenv("ADMIN_EMAIL", "sachin@gmail.com")
            admin_password = os.getenv("ADMIN_PASSWORD", "Thunder@123")
            admin_name = os.getenv("ADMIN_NAME", "Sachin - HRMS Super Administrator")
            force_reset = os.getenv("ADMIN_FORCE_RESET", "true").lower() in {"1", "true", "yes"}
            
            # Validate email format
            if "@" not in admin_email or "." not in admin_email.split("@")[1]:
                print(f"ERROR: Invalid email format: {admin_email}")
                print("Please set ADMIN_EMAIL environment variable with a valid email address")
                return
            
            # Validate password strength
            if len(admin_password) < 8:
                print(f"ERROR: Password too weak: Password must be at least 8 characters long")
                return
            
            print("Creating super admin with:")
            print(f"   Email: {admin_email}")
            print(f"   Name: {admin_name}")
            print(f"   Force Reset: {force_reset}")

            # Check if user already exists
            result = await session.execute(
                select(User).where(User.email == admin_email)
            )
            super_admin_user = result.scalar_one_or_none()
            
            if not super_admin_user:
                # Create super admin user
                super_admin_user = User(
                    email=admin_email,
                    hashed_password=get_password_hash(admin_password),
                    name=admin_name,
                    role=UserRole.SUPER_ADMIN,
                    is_active=True
                )
                session.add(super_admin_user)
                await session.commit()
                print("SUCCESS: Super admin user created successfully!")
                print(f"   Email: {admin_email}")
                print(f"   Password: {admin_password}")
                print("   Role: super_admin")
            else:
                # Optionally update existing user to super admin / reset password
                updated = False
                if super_admin_user.role != UserRole.SUPER_ADMIN:
                    super_admin_user.role = UserRole.SUPER_ADMIN
                    updated = True
                if not super_admin_user.is_active:
                    super_admin_user.is_active = True
                    updated = True
                if force_reset:
                    super_admin_user.hashed_password = get_password_hash(admin_password)
                    updated = True
                if super_admin_user.name != admin_name and os.getenv("ADMIN_UPDATE_NAME", "false").lower() in {"1", "true", "yes"}:
                    super_admin_user.name = admin_name
                    updated = True
                if updated:
                    await session.commit()
                    print("SUCCESS: Existing user updated to super admin")
                    print(f"   Email: {admin_email}")
                    if force_reset:
                        print(f"   Password reset to: {admin_password}")
                    print("   Role: super_admin")
                else:
                    print("INFO:  Super admin user already exists and is up-to-date")
                    print(f"   Email: {super_admin_user.email}")
                    print(f"   Role: {super_admin_user.role}")
        
        print("\nSuper admin creation process completed successfully!")
        
    except Exception as e:
        print(f"ERROR: Failed to create super admin user: {e}")
        print(f"TIP: Make sure the database is running and accessible")
        print(f"TIP: Check your DATABASE_URL configuration")
        raise
    finally:
        await engine.dispose()
        print("Database connection closed")

if __name__ == "__main__":
    asyncio.run(create_super_admin())
