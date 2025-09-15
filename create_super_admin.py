#!/usr/bin/env python3
"""
Script to create a super admin user in the HRMS database
This script can be run independently to add a super admin user.
"""

import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models import User, UserRole
from app.auth import get_password_hash
from app.database import DATABASE_URL

async def create_super_admin():
    """Create super admin user in the database."""
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    # Create async session factory
    AsyncSessionLocal = sessionmaker(
        engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    try:
        async with AsyncSessionLocal() as session:
            # Check if super admin user already exists
            result = await session.execute(
                select(User).where(User.email == "sachin@gmail.com")
            )
            super_admin_user = result.scalar_one_or_none()
            
            if not super_admin_user:
                # Create super admin user
                super_admin_user = User(
                    email="sachin@gmail.com",
                    hashed_password=get_password_hash("Thunder@123"),
                    name="Sachin - Super Administrator",
                    role=UserRole.SUPER_ADMIN,
                    is_active=True
                )
                session.add(super_admin_user)
                await session.commit()
                print("✅ Super admin user created successfully!")
                print("   Email: sachin@gmail.com")
                print("   Password: Thunder@123")
                print("   Role: super_admin")
            else:
                print("ℹ️  Super admin user already exists")
                print(f"   Email: {super_admin_user.email}")
                print(f"   Role: {super_admin_user.role}")
        
    except Exception as e:
        print(f"❌ Failed to create super admin user: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_super_admin())
